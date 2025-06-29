"""
Base collector abstract class for data acquisition engine.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CollectionResult:
    """Standard result format for all collectors"""
    source: str
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    quality_score: float
    collection_timestamp: datetime
    errors: List[str]
    warnings: List[str]

class BaseCollector(ABC):
    """Abstract base class for all data collectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limiter = self._init_rate_limiter()
        self.circuit_breaker = self._init_circuit_breaker()
        self.retry_handler = self._init_retry_handler()

    @abstractmethod
    async def collect(self, target: str, **kwargs) -> CollectionResult:
        """Main collection method - must be implemented by subclasses"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate collector configuration"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the data source is accessible"""
        pass

    def _init_rate_limiter(self):
        """Initialize rate limiter based on config"""
        # TODO: Implement rate limiter initialization
        pass

    def _init_circuit_breaker(self):
        """Initialize circuit breaker for fault tolerance"""
        # TODO: Implement circuit breaker initialization
        pass

    def _init_retry_handler(self):
        """Initialize retry handler with exponential backoff"""
        # TODO: Implement retry handler initialization
        pass
