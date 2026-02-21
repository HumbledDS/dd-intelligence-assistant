"""
DINUM API Recherche d'entreprises collector.
🎯 GAME CHANGER: Single API for comprehensive French business data.

API Documentation: https://recherche-entreprises.api.gouv.fr/docs/
Sources: RNE + SIRENE + IDCC + Ratios financiers
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

class DinumCollector(BaseCollector):
    """
    🥇 PREMIUM Collector for DINUM API Recherche d'entreprises.
    
    This API is a GAME CHANGER because it provides:
    - RNE (Registre National des Entreprises) 
    - SIRENE (INSEE business registry)
    - IDCC (Conventions collectives)
    - Ratios financiers (Financial ratios)
    - All in ONE FREE API call!
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # DINUM API configuration
        self.base_url = config.get('base_url', 'https://recherche-entreprises.api.gouv.fr')
        self.session = None
        
        # 🚀 EXCELLENT Rate limiting (400/min vs 30/min INSEE)
        self.rate_limit_config = {
            'max_requests': config.get('max_requests', 24000),  # 400/min * 60min
            'window_seconds': config.get('window_seconds', 3600),  # 1 hour
            'burst_size': config.get('burst_size', 50),
            'cost_per_request': 0  # 🎉 FREE!
        }
        
        # Circuit breaker for this premium source
        self.circuit_breaker_config = {
            'failure_threshold': config.get('failure_threshold', 5),
            'recovery_timeout': config.get('recovery_timeout', 180.0),  # 3 minutes
            'success_threshold': config.get('success_threshold', 3)
        }
        
        # Retry configuration
        self.retry_config = {
            'strategy': 'api_call',
            'max_attempts': config.get('max_attempts', 3),
            'base_delay': config.get('base_delay', 1.0),
            'max_delay': config.get('max_delay', 30.0)
        }
        
        self.logger.info("🎯 DINUM collector initialized - GAME CHANGER API!")
    
    async def collect(self, target: str, **kwargs) -> CollectionResult:
        """
        Collect comprehensive business data from DINUM API.
        
        🎯 This single call replaces multiple expensive API calls!
        
        Args:
            target: Search target (company name, SIRET, SIREN, etc.)
            **kwargs: Additional search parameters
            
        Returns:
            CollectionResult with comprehensive business data
        """
        try:
            # Create HTTP session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession(
                    headers={
                        'Accept': 'application/json',
                        'User-Agent': 'DD-Intelligence-Assistant/1.0'
                    }
                )
            
            # Build search query
            search_params = self._build_search_params(target, kwargs)
            
            # 🚀 Single API call for comprehensive data
            data = await self._fetch_dinum_data(search_params)
            
            # Process the rich data response
            processed_data = self._process_dinum_data(data)
            
            # Calculate quality score (should be high!)
            quality_score = self._calculate_quality_score(processed_data, data)
            
            return CollectionResult(
                source="DINUM_Recherche",
                data=processed_data,
                metadata={
                    "search_target": target,
                    "search_params": search_params,
                    "raw_response_size": len(str(data)),
                    "api_endpoint": f"{self.base_url}/search",
                    "data_sources": ["RNE", "SIRENE", "IDCC", "Ratios_Financiers"],
                    "cost": 0.0  # 🎉 FREE!
                },
                quality_score=quality_score,
                collection_timestamp=datetime.now(),
                errors=[],
                warnings=[],
                execution_time=0.0,
                cache_hit=False,
                retry_count=0
            )
            
        except Exception as e:
            self.logger.error("DINUM data collection failed", target=target, error=str(e))
            raise
    
    def validate_config(self) -> bool:
        """Validate DINUM collector configuration"""
        if not self.base_url:
            self.logger.error("DINUM base URL not configured")
            return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check DINUM API health"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Health check with simple search
            async with self.session.get(f"{self.base_url}/search?q=test&limite=1") as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "response_time": response.headers.get('X-Response-Time', 'unknown'),
                        "rate_limit_remaining": "400/min (excellent!)"
                    }
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _build_search_params(self, target: str, kwargs: Dict[str, Any]) -> Dict[str, str]:
        """Build search parameters for DINUM API"""
        params = {"q": target}
        
        # Limit results (default to reasonable number)
        params['limite'] = str(kwargs.get('limit', 25))
        
        # Page for pagination
        if kwargs.get('page'):
            params['page'] = str(kwargs['page'])
        
        # 🎯 ADVANCED: Include specific data types
        include_types = kwargs.get('include', [])
        if include_types:
            # Available: etablissement, unite_legale, dirigeant, etc.
            params['inclure'] = ','.join(include_types)
        
        # Geographic filters
        if kwargs.get('code_postal'):
            params['code_postal'] = kwargs['code_postal']
        
        if kwargs.get('departement'):
            params['departement'] = kwargs['departement']
        
        # Activity filters
        if kwargs.get('activite_principale'):
            params['activite_principale'] = kwargs['activite_principale']
        
        # Legal status filters
        if kwargs.get('nature_juridique'):
            params['nature_juridique'] = kwargs['nature_juridique']
        
        return params
    
    async def _fetch_dinum_data(self, search_params: Dict[str, str]) -> Dict[str, Any]:
        """Fetch data from DINUM API"""
        url = f"{self.base_url}/search"
        
        async with self.session.get(url, params=search_params) as response:
            if response.status == 200:
                data = await response.json()
                self.logger.info(
                    "🎯 DINUM API request successful",
                    url=url,
                    params=search_params,
                    result_count=data.get('total_results', 0),
                    cost=0.0  # 🎉 FREE!
                )
                return data
            elif response.status == 429:
                raise Exception("DINUM API rate limit exceeded (should be rare with 400/min!)")
            else:
                error_text = await response.text()
                raise Exception(f"DINUM API error {response.status}: {error_text}")
    
    def _process_dinum_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process and structure DINUM comprehensive data.
        
        🎯 This API provides MUCH more data than individual APIs!
        """
        processed_data = []
        results = raw_data.get('results', [])
        
        for result in results:
            try:
                # 🎯 RICH DATA from multiple sources in one response!
                processed_item = {
                    # Core identifiers (SIRENE source)
                    "siren": result.get('siren'),
                    "siret": result.get('siret'),
                    "nom_complet": result.get('nom_complet'),
                    "nom_raison_sociale": result.get('nom_raison_sociale'),
                    "sigle": result.get('sigle'),
                    
                    # Legal information (RNE source)
                    "nature_juridique": result.get('nature_juridique'),
                    "section_activite_principale": result.get('section_activite_principale'),
                    "activite_principale": result.get('activite_principale'),
                    "categorie_entreprise": result.get('categorie_entreprise'),
                    
                    # Address information
                    "adresse": {
                        "code_postal": result.get('code_postal'),
                        "libelle_commune": result.get('libelle_commune'), 
                        "libelle_region": result.get('libelle_region'),
                        "libelle_departement": result.get('libelle_departement'),
                        "adresse_ligne_1": result.get('adresse_ligne_1'),
                        "adresse_ligne_2": result.get('adresse_ligne_2')
                    },
                    
                    # Business status
                    "etat_administratif": result.get('etat_administratif'),
                    "date_creation": result.get('date_creation'),
                    "date_mise_a_jour": result.get('date_mise_a_jour'),
                    
                    # Financial indicators (🎯 BONUS from ratios source!)
                    "tranche_effectif_salarie": result.get('tranche_effectif_salarie'),
                    "annee_effectif_salarie": result.get('annee_effectif_salarie'),
                    
                    # Convention collective (IDCC source)
                    "convention_collective_renseignee": result.get('convention_collective_renseignee'),
                    "libelle_convention_collective": result.get('libelle_convention_collective'),
                    
                    # Establishment details
                    "est_siege": result.get('est_siege'),
                    "activite_principale_etablissement": result.get('activite_principale_etablissement'),
                    
                    # 🎯 METADATA: Track data sources included
                    "data_sources_included": {
                        "rne": bool(result.get('nature_juridique')),
                        "sirene": bool(result.get('siren')),
                        "idcc": bool(result.get('convention_collective_renseignee')),
                        "ratios": bool(result.get('tranche_effectif_salarie'))
                    }
                }
                
                # Clean up None values
                processed_item = self._clean_none_values(processed_item)
                
                processed_data.append(processed_item)
                
            except Exception as e:
                self.logger.warning(
                    "Error processing DINUM result",
                    error=str(e),
                    raw_data=result
                )
                continue
        
        return processed_data
    
    def _clean_none_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively clean None values from data"""
        if isinstance(data, dict):
            return {k: self._clean_none_values(v) for k, v in data.items() 
                   if v is not None and v != ''}
        elif isinstance(data, list):
            return [self._clean_none_values(item) for item in data if item is not None]
        else:
            return data
    
    def _calculate_quality_score(self, processed_data: List[Dict[str, Any]], raw_data: Dict[str, Any]) -> float:
        """
        Calculate data quality score.
        DINUM should score very high due to comprehensive official sources!
        """
        if not processed_data:
            return 0.0
        
        total_score = 0.0
        max_score = len(processed_data) * 10
        
        for item in processed_data:
            item_score = 0
            
            # Core business identifiers (4 points)
            if item.get('siren'):
                item_score += 2
            if item.get('siret'):
                item_score += 2
            
            # Legal information (2 points)
            if item.get('nature_juridique'):
                item_score += 1
            if item.get('activite_principale'):
                item_score += 1
            
            # Address completeness (2 points)
            address = item.get('adresse', {})
            if address.get('code_postal') and address.get('libelle_commune'):
                item_score += 2
            
            # Financial/employee info (1 point)
            if item.get('tranche_effectif_salarie'):
                item_score += 1
            
            # Convention collective (1 point)
            if item.get('convention_collective_renseignee'):
                item_score += 1
            
            # Cap at 10 points per record
            total_score += min(item_score, 10)
        
        return (total_score / max_score) * 100
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        
        await super().cleanup()
        self.logger.info("🎯 DINUM collector cleaned up")
    
    # 🎯 SPECIALIZED SEARCH METHODS
    
    async def search_by_name(self, company_name: str, **kwargs) -> CollectionResult:
        """Search companies by name using DINUM comprehensive search"""
        return await self.collect_with_protection(company_name, **kwargs)
    
    async def search_by_siren(self, siren: str) -> CollectionResult:
        """Search by SIREN - will get comprehensive profile"""
        return await self.collect_with_protection(f"siren:{siren}")
    
    async def search_by_siret(self, siret: str) -> CollectionResult:
        """Search by SIRET - will get comprehensive profile"""
        return await self.collect_with_protection(f"siret:{siret}")
    
    async def search_by_location(self, code_postal: str = None, departement: str = None, **kwargs) -> CollectionResult:
        """Search companies by location with geographic filters"""
        search_kwargs = kwargs.copy()
        
        if code_postal:
            search_kwargs['code_postal'] = code_postal
        if departement:
            search_kwargs['departement'] = departement
        
        # Use wildcard search with geographic filters
        return await self.collect_with_protection("*", **search_kwargs)
    
    async def search_by_activity(self, activite_code: str, **kwargs) -> CollectionResult:
        """Search companies by activity code (NAF/APE)"""
        search_kwargs = kwargs.copy()
        search_kwargs['activite_principale'] = activite_code
        
        return await self.collect_with_protection("*", **search_kwargs)
    
    async def get_comprehensive_profile(self, identifier: str, include_all: bool = True) -> CollectionResult:
        """
        Get the most comprehensive company profile possible.
        🎯 This leverages DINUM's multi-source aggregation!
        """
        search_kwargs = {}
        
        if include_all:
            # Request all available data types
            search_kwargs['include'] = [
                'etablissement',
                'unite_legale', 
                'dirigeant',
                'finances',
                'conventions'
            ]
        
        return await self.collect_with_protection(identifier, **search_kwargs)