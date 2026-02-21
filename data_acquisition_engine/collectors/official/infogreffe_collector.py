"""
Infogreffe data collector for French business registry and financial information.
Collects company financial data, legal documents, and business information.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog
from bs4 import BeautifulSoup

from ...core import BaseCollector, CollectionResult
from ...config.settings import settings

logger = structlog.get_logger(__name__)

class InfogreffeCollector(BaseCollector):
    """
    Collector for Infogreffe business and financial data.
    Implements web scraping and API access for French companies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Infogreffe-specific configuration
        self.base_url = config.get('base_url', 'https://www.infogreffe.fr')
        self.api_url = config.get('api_url', 'https://api.infogreffe.fr')
        self.session = None
        
        # Rate limiting specific to Infogreffe
        self.rate_limit_config = {
            'max_requests': config.get('max_requests', 100),  # Conservative limit for web scraping
            'window_seconds': config.get('window_seconds', 3600),  # 1 hour
            'burst_size': config.get('burst_size', 5),
            'cost_per_request': config.get('cost_per_request', 1)
        }
        
        # Circuit breaker specific to Infogreffe
        self.circuit_breaker_config = {
            'failure_threshold': config.get('failure_threshold', 3),
            'recovery_timeout': config.get('recovery_timeout', 600.0),  # 10 minutes
            'success_threshold': config.get('success_threshold', 2)
        }
        
        # Retry configuration for web scraping
        self.retry_config = {
            'strategy': 'web_scraping',
            'max_attempts': config.get('max_attempts', 3),
            'base_delay': config.get('base_delay', 5.0),
            'max_delay': config.get('max_delay', 120.0)
        }
        
        # User agent for web scraping
        self.user_agent = config.get('user_agent', 'Mozilla/5.0 (compatible; DD-Intelligence-Assistant/1.0)')
        
        self.logger.info("Infogreffe collector initialized")
    
    async def collect(self, target: str, **kwargs) -> CollectionResult:
        """
        Collect business data from Infogreffe.
        
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
                        'User-Agent': self.user_agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                )
            
            # Determine search type and collect data
            search_type = kwargs.get('search_type', 'company_name')
            
            if search_type == 'company_name':
                data = await self._search_by_company_name(target, **kwargs)
            elif search_type == 'siret':
                data = await self._search_by_siret(target, **kwargs)
            elif search_type == 'siren':
                data = await self._search_by_siren(target, **kwargs)
            else:
                raise ValueError(f"Unsupported search type: {search_type}")
            
            # Process and validate data
            processed_data = self._process_infogreffe_data(data)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(processed_data, data)
            
            return CollectionResult(
                source="Infogreffe",
                data=processed_data,
                metadata={
                    "search_target": target,
                    "search_type": search_type,
                    "raw_response_size": len(str(data)),
                    "source_url": self.base_url
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
            self.logger.error("Infogreffe data collection failed", target=target, error=str(e))
            raise
    
    def validate_config(self) -> bool:
        """Validate Infogreffe collector configuration"""
        if not self.base_url:
            self.logger.error("Infogreffe base URL not configured")
            return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Infogreffe website health"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(headers={'User-Agent': self.user_agent})
            
            # Make a simple health check request
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "response_time": response.headers.get('X-Response-Time', 'unknown'),
                        "content_length": len(await response.text())
                    }
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _search_by_company_name(self, company_name: str, **kwargs) -> Dict[str, Any]:
        """Search companies by name on Infogreffe"""
        search_url = f"{self.base_url}/recherche-entreprise"
        
        # Build search form data
        form_data = {
            'recherche': company_name,
            'type': 'entreprise'
        }
        
        # Add additional filters
        if kwargs.get('postal_code'):
            form_data['codePostal'] = kwargs['postal_code']
        if kwargs.get('city'):
            form_data['ville'] = kwargs['city']
        
        async with self.session.post(search_url, data=form_data) as response:
            if response.status == 200:
                html_content = await response.text()
                return self._parse_search_results(html_content, company_name)
            else:
                raise Exception(f"Infogreffe search failed: HTTP {response.status}")
    
    async def _search_by_siret(self, siret: str, **kwargs) -> Dict[str, Any]:
        """Search company by SIRET number"""
        # Direct access to company page if SIRET is known
        company_url = f"{self.base_url}/entreprise/{siret}"
        
        async with self.session.get(company_url) as response:
            if response.status == 200:
                html_content = await response.text()
                return self._parse_company_page(html_content, siret)
            else:
                # Fallback to search
                return await self._search_by_company_name(siret, search_type='siret')
    
    async def _search_by_siren(self, siren: str, **kwargs) -> Dict[str, Any]:
        """Search company by SIREN number"""
        # Try direct access first
        company_url = f"{self.base_url}/entreprise/{siren}"
        
        async with self.session.get(company_url) as response:
            if response.status == 200:
                html_content = await response.text()
                return self._parse_company_page(html_content, siren)
            else:
                # Fallback to search
                return await self._search_by_company_name(siren, search_type='siren')
    
    def _parse_search_results(self, html_content: str, search_term: str) -> Dict[str, Any]:
        """Parse search results HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        results = {
            "search_term": search_term,
            "total_results": 0,
            "companies": []
        }
        
        # Find search results container
        results_container = soup.find('div', class_='resultats-recherche')
        if not results_container:
            return results
        
        # Extract company links
        company_links = results_container.find_all('a', href=True)
        
        for link in company_links[:10]:  # Limit to first 10 results
            company_info = self._extract_company_info_from_link(link)
            if company_info:
                results["companies"].append(company_info)
        
        results["total_results"] = len(results["companies"])
        return results
    
    def _parse_company_page(self, html_content: str, identifier: str) -> Dict[str, Any]:
        """Parse individual company page HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        company_data = {
            "identifier": identifier,
            "company_info": {},
            "financial_data": {},
            "legal_documents": []
        }
        
        # Extract company information
        company_info_section = soup.find('div', class_='informations-entreprise')
        if company_info_section:
            company_data["company_info"] = self._extract_company_info(company_info_section)
        
        # Extract financial data
        financial_section = soup.find('div', class_='donnees-financieres')
        if financial_section:
            company_data["financial_data"] = self._extract_financial_data(financial_section)
        
        # Extract legal documents
        documents_section = soup.find('div', class_='documents-legaux')
        if documents_section:
            company_data["legal_documents"] = self._extract_legal_documents(documents_section)
        
        return company_data
    
    def _extract_company_info_from_link(self, link_element) -> Optional[Dict[str, Any]]:
        """Extract basic company info from search result link"""
        try:
            # Extract company name
            company_name = link_element.get_text(strip=True)
            
            # Extract SIRET/SIREN from href if possible
            href = link_element.get('href', '')
            identifier = href.split('/')[-1] if href else None
            
            return {
                "company_name": company_name,
                "identifier": identifier,
                "detail_url": href if href.startswith('http') else f"{self.base_url}{href}"
            }
        except Exception as e:
            self.logger.warning("Error extracting company info from link", error=str(e))
            return None
    
    def _extract_company_info(self, info_section) -> Dict[str, Any]:
        """Extract detailed company information"""
        company_info = {}
        
        try:
            # Extract SIRET/SIREN
            siret_elem = info_section.find('span', string=lambda text: 'SIRET' in text if text else False)
            if siret_elem:
                siret_value = siret_elem.find_next_sibling('span')
                if siret_value:
                    company_info["siret"] = siret_value.get_text(strip=True)
            
            # Extract company name
            name_elem = info_section.find('h1') or info_section.find('h2')
            if name_elem:
                company_info["company_name"] = name_elem.get_text(strip=True)
            
            # Extract address
            address_elem = info_section.find('div', class_='adresse')
            if address_elem:
                company_info["address"] = address_elem.get_text(strip=True)
            
            # Extract legal status
            status_elem = info_section.find('span', string=lambda text: 'Forme juridique' in text if text else False)
            if status_elem:
                status_value = status_elem.find_next_sibling('span')
                if status_value:
                    company_info["legal_status"] = status_value.get_text(strip=True)
            
            # Extract creation date
            date_elem = info_section.find('span', string=lambda text: 'Date de création' in text if text else False)
            if date_elem:
                date_value = date_elem.find_next_sibling('span')
                if date_value:
                    company_info["creation_date"] = date_value.get_text(strip=True)
            
        except Exception as e:
            self.logger.warning("Error extracting company info", error=str(e))
        
        return company_info
    
    def _extract_financial_data(self, financial_section) -> Dict[str, Any]:
        """Extract financial data from company page"""
        financial_data = {}
        
        try:
            # Extract turnover
            turnover_elem = financial_section.find('span', string=lambda text: 'Chiffre d\'affaires' in text if text else False)
            if turnover_elem:
                turnover_value = turnover_elem.find_next_sibling('span')
                if turnover_value:
                    financial_data["turnover"] = turnover_value.get_text(strip=True)
            
            # Extract profit
            profit_elem = financial_section.find('span', string=lambda text: 'Résultat net' in text if text else False)
            if profit_elem:
                profit_value = profit_elem.find_next_sibling('span')
                if profit_value:
                    financial_data["net_profit"] = profit_value.get_text(strip=True)
            
            # Extract employee count
            employees_elem = financial_section.find('span', string=lambda text: 'Effectif' in text if text else False)
            if employees_elem:
                employees_value = employees_elem.find_next_sibling('span')
                if employees_value:
                    financial_data["employee_count"] = employees_value.get_text(strip=True)
            
        except Exception as e:
            self.logger.warning("Error extracting financial data", error=str(e))
        
        return financial_data
    
    def _extract_legal_documents(self, documents_section) -> List[Dict[str, Any]]:
        """Extract legal documents information"""
        documents = []
        
        try:
            # Find document links
            doc_links = documents_section.find_all('a', href=True)
            
            for link in doc_links:
                doc_info = {
                    "title": link.get_text(strip=True),
                    "url": link.get('href'),
                    "type": self._determine_document_type(link.get_text(strip=True))
                }
                documents.append(doc_info)
            
        except Exception as e:
            self.logger.warning("Error extracting legal documents", error=str(e))
        
        return documents
    
    def _determine_document_type(self, document_title: str) -> str:
        """Determine document type based on title"""
        title_lower = document_title.lower()
        
        if 'bilan' in title_lower:
            return 'balance_sheet'
        elif 'compte de résultat' in title_lower:
            return 'income_statement'
        elif 'rapport' in title_lower:
            return 'annual_report'
        elif 'statuts' in title_lower:
            return 'articles_of_association'
        else:
            return 'other'
    
    def _process_infogreffe_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and clean Infogreffe raw data"""
        processed_data = []
        
        if "companies" in raw_data:
            # Search results
            for company in raw_data["companies"]:
                processed_item = {
                    "source": "Infogreffe",
                    "company_name": company.get("company_name"),
                    "identifier": company.get("identifier"),
                    "detail_url": company.get("detail_url"),
                    "data_type": "search_result"
                }
                processed_data.append(processed_item)
        
        elif "company_info" in raw_data:
            # Individual company page
            company_info = raw_data["company_info"]
            financial_data = raw_data.get("financial_data", {})
            
            processed_item = {
                "source": "Infogreffe",
                "siret": company_info.get("siret"),
                "company_name": company_info.get("company_name"),
                "address": company_info.get("address"),
                "legal_status": company_info.get("legal_status"),
                "creation_date": company_info.get("creation_date"),
                "turnover": financial_data.get("turnover"),
                "net_profit": financial_data.get("net_profit"),
                "employee_count": financial_data.get("employee_count"),
                "legal_documents_count": len(raw_data.get("legal_documents", [])),
                "data_type": "company_detail"
            }
            processed_data.append(processed_item)
        
        return processed_data
    
    def _calculate_quality_score(self, processed_data: List[Dict[str, Any]], raw_data: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        if not processed_data:
            return 0.0
        
        total_score = 0.0
        max_score = len(processed_data) * 10  # 10 points per record
        
        for item in processed_data:
            item_score = 0
            
            # Score based on data type
            if item.get("data_type") == "company_detail":
                # Company detail page has more information
                required_fields = ['company_name', 'siret']
                for field in required_fields:
                    if item.get(field):
                        item_score += 2
                
                # Additional fields
                additional_fields = ['address', 'legal_status', 'creation_date']
                for field in additional_fields:
                    if item.get(field):
                        item_score += 1
                
                # Financial data
                financial_fields = ['turnover', 'net_profit', 'employee_count']
                for field in financial_fields:
                    if item.get(field):
                        item_score += 1
                
            else:
                # Search result
                required_fields = ['company_name', 'identifier']
                for field in required_fields:
                    if item.get(field):
                        item_score += 3
                
                if item.get("detail_url"):
                    item_score += 2
            
            total_score += min(item_score, 10)  # Cap at 10 points per record
        
        return (total_score / max_score) * 100
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        
        await super().cleanup()
        self.logger.info("Infogreffe collector cleaned up")
    
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
    
    async def get_company_details(self, identifier: str) -> CollectionResult:
        """Get detailed company information"""
        return await self.collect_with_protection(
            identifier, 
            search_type='siret'  # Use SIRET search for detailed info
        )
