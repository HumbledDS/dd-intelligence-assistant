"""
DataGouv (French Open Data Platform) data collector.
Collects various types of public data from the French government's open data platform.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog
from urllib.parse import urljoin, urlparse

from ...core import BaseCollector, CollectionResult
from ...config.settings import settings

logger = structlog.get_logger(__name__)

class DataGouvCollector(BaseCollector):
    """
    Collector for French open data from DataGouv platform.
    Implements access to various datasets including business, economic, and public data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # DataGouv-specific configuration
        self.base_url = config.get('base_url', 'https://www.data.gouv.fr/api/1')
        self.datasets_url = config.get('datasets_url', 'https://www.data.gouv.fr/api/1/datasets')
        self.resources_url = config.get('resources_url', 'https://www.data.gouv.fr/api/1/datasets')
        self.api_key = config.get('api_key', settings.datagouv_api_key)
        self.session = None
        
        # Rate limiting specific to DataGouv API
        self.rate_limit_config = {
            'max_requests': config.get('max_requests', 100),  # Conservative limit for public API
            'window_seconds': config.get('window_seconds', 3600),  # 1 hour
            'burst_size': config.get('burst_size', 10),
            'cost_per_request': config.get('cost_per_request', 1)
        }
        
        # Circuit breaker specific to DataGouv
        self.circuit_breaker_config = {
            'failure_threshold': config.get('failure_threshold', 5),
            'recovery_timeout': config.get('recovery_timeout', 300.0),  # 5 minutes
            'success_threshold': config.get('success_threshold', 2)
        }
        
        # Retry configuration for DataGouv API
        self.retry_config = {
            'strategy': 'api_call',
            'max_attempts': config.get('max_attempts', 3),
            'base_delay': config.get('base_delay', 2.0),
            'max_delay': config.get('max_delay', 60.0)
        }
        
        # Supported dataset categories
        self.supported_categories = [
            'entreprises', 'economie', 'finance', 'administration',
            'territoire', 'sante', 'education', 'transport'
        ]
        
        self.logger.info("DataGouv collector initialized")
    
    async def collect(self, target: str, **kwargs) -> CollectionResult:
        """
        Collect data from DataGouv platform.
        
        Args:
            target: Search target (dataset name, category, organization, etc.)
            **kwargs: Additional search parameters
            
        Returns:
            CollectionResult with open data information
        """
        try:
            # Create HTTP session if not exists
            if not self.session:
                headers = {
                    'Accept': 'application/json',
                    'User-Agent': 'DD-Intelligence-Assistant/1.0'
                }
                
                # Add API key if available
                if self.api_key:
                    headers['Authorization'] = f'Bearer {self.api_key}'
                    self.logger.info("Using DataGouv API key for authentication")
                else:
                    self.logger.warning("No DataGouv API key provided, using public access")
                
                self.session = aiohttp.ClientSession(headers=headers)
            
            # Determine search type and collect data
            search_type = kwargs.get('search_type', 'dataset_search')
            
            if search_type == 'dataset_search':
                data = await self._search_datasets(target, **kwargs)
            elif search_type == 'category_search':
                data = await self._search_by_category(target, **kwargs)
            elif search_type == 'organization_search':
                data = await self._search_by_organization(target, **kwargs)
            elif search_type == 'resource_download':
                data = await self._download_resource(target, **kwargs)
            else:
                raise ValueError(f"Unsupported search type: {search_type}")
            
            # Process and validate data
            processed_data = self._process_datagouv_data(data, search_type)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(processed_data, data)
            
            return CollectionResult(
                source="DataGouv",
                data=processed_data,
                metadata={
                    "search_target": target,
                    "search_type": search_type,
                    "raw_response_size": len(str(data)),
                    "api_endpoint": self.base_url,
                    "api_key_used": bool(self.api_key)
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
            self.logger.error("DataGouv data collection failed", target=target, error=str(e))
            raise
    
    def validate_config(self) -> bool:
        """Validate DataGouv collector configuration"""
        if not self.base_url:
            self.logger.error("DataGouv base URL not configured")
            return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check DataGouv API health"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Make a simple health check request
            async with self.session.get(f"{self.datasets_url}?page=1&page_size=1") as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "response_time": response.headers.get('X-Response-Time', 'unknown'),
                        "api_version": "1.0"
                    }
                elif response.status == 429:
                    return {"status": "unhealthy", "error": "Rate limit exceeded"}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _search_datasets(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search datasets by query string"""
        search_url = f"{self.datasets_url}/search"
        
        params = {
            'q': query,
            'page': kwargs.get('page', 1),
            'page_size': kwargs.get('page_size', 20)
        }
        
        # Add filters
        if kwargs.get('category'):
            params['facets'] = f"category:{kwargs['category']}"
        
        if kwargs.get('organization'):
            params['organization'] = kwargs['organization']
        
        if kwargs.get('format'):
            params['format'] = kwargs['format']
        
        async with self.session.get(search_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                self.logger.info(
                    "Dataset search successful",
                    query=query,
                    result_count=data.get('total', 0)
                )
                return data
            else:
                error_text = await response.text()
                raise Exception(f"Dataset search failed: HTTP {response.status}: {error_text}")
    
    async def _search_by_category(self, category: str, **kwargs) -> Dict[str, Any]:
        """Search datasets by category"""
        if category not in self.supported_categories:
            raise ValueError(f"Unsupported category: {category}. Supported: {self.supported_categories}")
        
        search_url = f"{self.datasets_url}/search"
        
        params = {
            'facets': f"category:{category}",
            'page': kwargs.get('page', 1),
            'page_size': kwargs.get('page_size', 20)
        }
        
        async with self.session.get(search_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                self.logger.info(
                    "Category search successful",
                    category=category,
                    result_count=data.get('total', 0)
                )
                return data
            else:
                error_text = await response.text()
                raise Exception(f"Category search failed: HTTP {response.status}: {error_text}")
    
    async def _search_by_organization(self, organization: str, **kwargs) -> Dict[str, Any]:
        """Search datasets by organization"""
        search_url = f"{self.datasets_url}/search"
        
        params = {
            'organization': organization,
            'page': kwargs.get('page', 1),
            'page_size': kwargs.get('page_size', 20)
        }
        
        async with self.session.get(search_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                self.logger.info(
                    "Organization search successful",
                    organization=organization,
                    result_count=data.get('total', 0)
                )
                return data
            else:
                error_text = await response.text()
                raise Exception(f"Organization search failed: HTTP {response.status}: {error_text}")
    
    async def _download_resource(self, resource_url: str, **kwargs) -> Dict[str, Any]:
        """Download a specific resource from DataGouv"""
        try:
            # Validate URL
            parsed_url = urlparse(resource_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid resource URL")
            
            # Download the resource
            async with self.session.get(resource_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'json' in content_type:
                        data = await response.json()
                    elif 'csv' in content_type or 'text' in content_type:
                        data = await response.text()
                    else:
                        # For binary files, just get metadata
                        data = {
                            "content_type": content_type,
                            "content_length": response.headers.get('content-length'),
                            "filename": resource_url.split('/')[-1]
                        }
                    
                    self.logger.info(
                        "Resource download successful",
                        url=resource_url,
                        content_type=content_type
                    )
                    
                    return {
                        "resource_url": resource_url,
                        "content_type": content_type,
                        "data": data,
                        "headers": dict(response.headers)
                    }
                else:
                    raise Exception(f"Resource download failed: HTTP {response.status}")
        
        except Exception as e:
            self.logger.error("Resource download failed", url=resource_url, error=str(e))
            raise
    
    def _process_datagouv_data(self, raw_data: Dict[str, Any], search_type: str) -> List[Dict[str, Any]]:
        """Process and clean DataGouv raw data"""
        processed_data = []
        
        if search_type in ['dataset_search', 'category_search', 'organization_search']:
            # Process dataset search results
            datasets = raw_data.get('data', [])
            
            for dataset in datasets:
                try:
                    processed_item = {
                        "dataset_id": dataset.get('id'),
                        "title": dataset.get('title'),
                        "description": dataset.get('description'),
                        "category": dataset.get('category'),
                        "organization": dataset.get('organization', {}).get('name'),
                        "organization_id": dataset.get('organization', {}).get('id'),
                        "tags": dataset.get('tags', []),
                        "created_at": dataset.get('created_at'),
                        "last_modified": dataset.get('last_modified'),
                        "resources_count": len(dataset.get('resources', [])),
                        "resources": self._process_resources(dataset.get('resources', [])),
                        "dataset_url": dataset.get('page'),
                        "api_url": dataset.get('uri')
                    }
                    
                    # Clean up None values
                    processed_item = {k: v for k, v in processed_item.items() if v is not None}
                    
                    processed_data.append(processed_item)
                    
                except Exception as e:
                    self.logger.warning(
                        "Error processing dataset",
                        error=str(e),
                        dataset_id=dataset.get('id')
                    )
                    continue
        
        elif search_type == 'resource_download':
            # Process downloaded resource
            processed_item = {
                "resource_url": raw_data.get('resource_url'),
                "content_type": raw_data.get('content_type'),
                "content_length": raw_data.get('data', {}).get('content_length'),
                "filename": raw_data.get('data', {}).get('filename'),
                "download_timestamp": datetime.now().isoformat()
            }
            
            # Add data preview for text-based content
            if isinstance(raw_data.get('data'), str):
                content = raw_data['data']
                processed_item['data_preview'] = content[:500] + '...' if len(content) > 500 else content
                processed_item['data_length'] = len(content)
            
            processed_data.append(processed_item)
        
        return processed_data
    
    def _process_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process dataset resources"""
        processed_resources = []
        
        for resource in resources:
            try:
                processed_resource = {
                    "id": resource.get('id'),
                    "title": resource.get('title'),
                    "description": resource.get('description'),
                    "format": resource.get('format'),
                    "url": resource.get('url'),
                    "file_size": resource.get('filesize'),
                    "mime_type": resource.get('mime'),
                    "download_count": resource.get('metrics', {}).get('downloads', 0),
                    "last_modified": resource.get('last_modified')
                }
                
                # Clean up None values
                processed_resource = {k: v for k, v in processed_resource.items() if v is not None}
                processed_resources.append(processed_resource)
                
            except Exception as e:
                self.logger.warning(
                    "Error processing resource",
                    error=str(e),
                    resource_id=resource.get('id')
                )
                continue
        
        return processed_resources
    
    def _calculate_quality_score(self, processed_data: List[Dict[str, Any]], raw_data: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        if not processed_data:
            return 0.0
        
        total_score = 0.0
        max_score = len(processed_data) * 10  # 10 points per record
        
        for item in processed_data:
            item_score = 0
            
            # Score based on completeness
            required_fields = ['title', 'description']
            for field in required_fields:
                if item.get(field):
                    item_score += 2
            
            # Score based on metadata completeness
            metadata_fields = ['category', 'organization', 'tags', 'resources_count']
            for field in metadata_fields:
                if item.get(field):
                    item_score += 1
            
            # Score based on resource information
            if item.get('resources') and len(item['resources']) > 0:
                item_score += 2
            
            # Score based on timestamps
            if item.get('created_at'):
                item_score += 1
            if item.get('last_modified'):
                item_score += 1
            
            total_score += min(item_score, 10)  # Cap at 10 points per record
        
        return (total_score / max_score) * 100
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        
        await super().cleanup()
        self.logger.info("DataGouv collector cleaned up")
    
    # Convenience methods for common use cases
    async def search_business_datasets(self, query: str = None, **kwargs) -> CollectionResult:
        """Search for business-related datasets"""
        if query:
            return await self.collect_with_protection(
                query, 
                search_type='dataset_search', 
                category='entreprises',
                **kwargs
            )
        else:
            return await self.collect_with_protection(
                'entreprises', 
                search_type='category_search', 
                **kwargs
            )
    
    async def search_economic_datasets(self, query: str = None, **kwargs) -> CollectionResult:
        """Search for economic and financial datasets"""
        if query:
            return await self.collect_with_protection(
                query, 
                search_type='dataset_search', 
                category='economie',
                **kwargs
            )
        else:
            return await self.collect_with_protection(
                'economie', 
                search_type='category_search', 
                **kwargs
            )
    
    async def search_organization_datasets(self, organization: str, **kwargs) -> CollectionResult:
        """Search datasets from a specific organization"""
        return await self.collect_with_protection(
            organization, 
            search_type='organization_search', 
            **kwargs
        )
    
    async def download_dataset_resource(self, resource_url: str, **kwargs) -> CollectionResult:
        """Download a specific dataset resource"""
        return await self.collect_with_protection(
            resource_url, 
            search_type='resource_download', 
            **kwargs
        )
    
    def get_supported_categories(self) -> List[str]:
        """Get list of supported dataset categories"""
        return self.supported_categories.copy()
    
    async def get_popular_datasets(self, limit: int = 10) -> CollectionResult:
        """Get popular datasets based on download counts"""
        # This would require additional API calls to get metrics
        # For now, we'll search for datasets with a generic query
        return await self.collect_with_protection(
            'popular', 
            search_type='dataset_search', 
            page_size=limit
        )
