"""
INSEE (French National Institute of Statistics and Economic Studies) data collector.
Collects business registry information from INSEE APIs.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

from ...core import BaseCollector, CollectionResult
from ...config.settings import settings

logger = structlog.get_logger(__name__)

class InseeCollector(BaseCollector):
    """
    Collector for INSEE business registry data.
    Implements the SIRENE database API for French companies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # INSEE-specific configuration
        self.api_key = config.get('api_key', settings.insee_api_key)
        self.base_url = config.get('base_url', 'https://api.insee.fr/entreprises/sirene/V3')
        self.session = None
        
        # Rate limiting specific to INSEE API
        self.rate_limit_config = {
            'max_requests': config.get('max_requests', 1000),  # INSEE allows 1000 requests per day
            'window_seconds': config.get('window_seconds', 86400),  # 24 hours
            'burst_size': config.get('burst_size', 10),
            'cost_per_request': config.get('cost_per_request', 1)
        }
        
        # Circuit breaker specific to INSEE
        self.circuit_breaker_config = {
            'failure_threshold': config.get('failure_threshold', 3),
            'recovery_timeout': config.get('recovery_timeout', 300.0),  # 5 minutes
            'success_threshold': config.get('success_threshold', 2)
        }
        
        # Retry configuration for INSEE API
        self.retry_config = {
            'strategy': 'api_call',
            'max_attempts': config.get('max_attempts', 3),
            'base_delay': config.get('base_delay', 2.0),
            'max_delay': config.get('max_delay', 60.0)
        }
        
        self.logger.info("INSEE collector initialized", api_key_configured=bool(self.api_key))
    
    async def collect(self, target: str, **kwargs) -> CollectionResult:
        """
        Collect business data from INSEE SIRENE database.
        
        Args:
            target: Search target (company name, SIRET, SIREN, etc.)
            **kwargs: Additional search parameters
            
        Returns:
            CollectionResult with business data
        """
        try:
            # Create HTTP session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession(
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Accept': 'application/json',
                        'User-Agent': 'DD-Intelligence-Assistant/1.0'
                    }
                )
            
            # Determine search type and build query
            search_type = kwargs.get('search_type', 'company_name')
            query_params = self._build_query_params(target, search_type, kwargs)
            
            # Make API request
            data = await self._fetch_insee_data(query_params)
            
            # Process and validate data
            processed_data = self._process_insee_data(data)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(processed_data, data)
            
            return CollectionResult(
                source="INSEE",
                data=processed_data,
                metadata={
                    "search_target": target,
                    "search_type": search_type,
                    "query_params": query_params,
                    "raw_response_size": len(str(data)),
                    "api_endpoint": f"{self.base_url}/siret"
                },
                quality_score=quality_score,
                collection_timestamp=datetime.now(),
                errors=[],
                warnings=[],
                execution_time=0.0,  # Will be set by collect_with_protection
                cache_hit=False,
                retry_count=0
            )
            
        except Exception as e:
            self.logger.error("INSEE data collection failed", target=target, error=str(e))
            raise
    
    def validate_config(self) -> bool:
        """Validate INSEE collector configuration"""
        if not self.api_key:
            self.logger.error("INSEE API key not configured")
            return False
        
        if not self.base_url:
            self.logger.error("INSEE base URL not configured")
            return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check INSEE API health"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
            
            # Make a simple health check request
            async with self.session.get(f"{self.base_url}/siret?q=test") as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "response_time": response.headers.get('X-Response-Time', 'unknown'),
                        "rate_limit_remaining": response.headers.get('X-RateLimit-Remaining', 'unknown')
                    }
                elif response.status == 401:
                    return {"status": "unhealthy", "error": "Authentication failed"}
                elif response.status == 429:
                    return {"status": "unhealthy", "error": "Rate limit exceeded"}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _build_query_params(self, target: str, search_type: str, kwargs: Dict[str, Any]) -> Dict[str, str]:
        """Build query parameters for INSEE API"""
        params = {}
        
        if search_type == 'company_name':
            params['q'] = target
        elif search_type == 'siret':
            params['q'] = f"siret:{target}"
        elif search_type == 'siren':
            params['q'] = f"siren:{target}"
        elif search_type == 'postal_code':
            params['q'] = f"codePostalEtablissement:{target}"
        elif search_type == 'city':
            params['q'] = f"libelleCommuneEtablissement:{target}"
        
        # Add additional filters
        if kwargs.get('active_only'):
            params['q'] += " AND etatAdministratifEtablissement:A"
        
        if kwargs.get('limit'):
            params['nombre'] = str(kwargs['limit'])
        else:
            params['nombre'] = '100'  # Default limit
        
        if kwargs.get('start'):
            params['debut'] = str(kwargs['start'])
        
        return params
    
    async def _fetch_insee_data(self, query_params: Dict[str, str]) -> Dict[str, Any]:
        """Fetch data from INSEE API"""
        url = f"{self.base_url}/siret"
        
        async with self.session.get(url, params=query_params) as response:
            if response.status == 200:
                data = await response.json()
                self.logger.info(
                    "INSEE API request successful",
                    url=url,
                    params=query_params,
                    result_count=len(data.get('etablissements', []))
                )
                return data
            elif response.status == 401:
                raise Exception("INSEE API authentication failed")
            elif response.status == 429:
                raise Exception("INSEE API rate limit exceeded")
            else:
                error_text = await response.text()
                raise Exception(f"INSEE API error {response.status}: {error_text}")
    
    def _process_insee_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and clean INSEE raw data"""
        processed_data = []
        etablissements = raw_data.get('etablissements', [])
        
        for etablissement in etablissements:
            try:
                # Extract key information
                processed_item = {
                    "siret": etablissement.get('siret'),
                    "siren": etablissement.get('siren'),
                    "company_name": etablissement.get('uniteLegale', {}).get('denominationUniteLegale'),
                    "trading_name": etablissement.get('uniteLegale', {}).get('denominationUsuelle1UniteLegale'),
                    "legal_status": etablissement.get('uniteLegale', {}).get('categorieJuridiqueUniteLegale'),
                    "activity_code": etablissement.get('uniteLegale', {}).get('activitePrincipaleUniteLegale'),
                    "activity_label": etablissement.get('uniteLegale', {}).get('libelleActivitePrincipaleUniteLegale'),
                    "address": {
                        "street": etablissement.get('adresseEtablissement', {}).get('numeroVoieEtablissement'),
                        "street_type": etablissement.get('adresseEtablissement', {}).get('typeVoieEtablissement'),
                        "street_name": etablissement.get('adresseEtablissement', {}).get('libelleVoieEtablissement'),
                        "postal_code": etablissement.get('adresseEtablissement', {}).get('codePostalEtablissement'),
                        "city": etablissement.get('adresseEtablissement', {}).get('libelleCommuneEtablissement'),
                        "country": etablissement.get('adresseEtablissement', {}).get('libellePaysEtrangerEtablissement')
                    },
                    "establishment_status": etablissement.get('etatAdministratifEtablissement'),
                    "establishment_type": etablissement.get('typeEtablissement'),
                    "creation_date": etablissement.get('dateCreationEtablissement'),
                    "last_update": etablissement.get('dateDerniereTraitementEtablissement'),
                    "employee_count": etablissement.get('trancheEffectifsEtablissement'),
                    "employee_count_label": etablissement.get('libelleTrancheEffectifsEtablissement')
                }
                
                # Clean up None values
                processed_item = {k: v for k, v in processed_item.items() if v is not None}
                
                processed_data.append(processed_item)
                
            except Exception as e:
                self.logger.warning(
                    "Error processing establishment data",
                    error=str(e),
                    raw_data=etablissement
                )
                continue
        
        return processed_data
    
    def _calculate_quality_score(self, processed_data: List[Dict[str, Any]], raw_data: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        if not processed_data:
            return 0.0
        
        total_score = 0.0
        max_score = len(processed_data) * 10  # 10 points per record
        
        for item in processed_data:
            item_score = 0
            
            # Score based on completeness
            required_fields = ['siret', 'siren', 'company_name']
            for field in required_fields:
                if item.get(field):
                    item_score += 2
            
            # Score based on address completeness
            address = item.get('address', {})
            address_fields = ['street', 'postal_code', 'city']
            for field in address_fields:
                if address.get(field):
                    item_score += 1
            
            # Score based on activity information
            if item.get('activity_code'):
                item_score += 1
            if item.get('activity_label'):
                item_score += 1
            
            # Score based on status information
            if item.get('establishment_status'):
                item_score += 1
            
            total_score += min(item_score, 10)  # Cap at 10 points per record
        
        return (total_score / max_score) * 100
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        
        await super().cleanup()
        self.logger.info("INSEE collector cleaned up")
    
    async def search_by_company_name(self, company_name: str, **kwargs) -> CollectionResult:
        """Search companies by name"""
        return await self.collect_with_protection(
            company_name, 
            search_type='company_name', 
            **kwargs
        )
    
    async def search_by_siret(self, siret: str) -> CollectionResult:
        """Search company by SIRET number"""
        return await self.collect_with_protection(
            siret, 
            search_type='siret'
        )
    
    async def search_by_siren(self, siren: str) -> CollectionResult:
        """Search company by SIREN number"""
        return await self.collect_with_protection(
            siren, 
            search_type='siren'
        )
    
    async def search_by_location(self, postal_code: str = None, city: str = None, **kwargs) -> CollectionResult:
        """Search companies by location"""
        if postal_code:
            return await self.collect_with_protection(
                postal_code, 
                search_type='postal_code', 
                **kwargs
            )
        elif city:
            return await self.collect_with_protection(
                city, 
                search_type='city', 
                **kwargs
            )
        else:
            raise ValueError("Either postal_code or city must be provided")
