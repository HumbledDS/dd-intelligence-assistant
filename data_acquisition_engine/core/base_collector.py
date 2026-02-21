"""
Base collector abstract class for data acquisition engine.
Integrates with rate limiting, circuit breaker, retry handling, and event routing.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

from .rate_limiter import RateLimiter, RateLimitConfig
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .retry_handler import RetryHandler, RetryConfig, RetryConfigs
from .event_router import EventType, EventPriority, EventBuilder, publish_event

logger = structlog.get_logger(__name__)

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
    execution_time: float
    cache_hit: bool = False
    retry_count: int = 0

class BaseCollector(ABC):
    """Abstract base class for all data collectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger.bind(component="base_collector", source=self.__class__.__name__)
        
        # Initialize core components
        self.rate_limiter = self._init_rate_limiter()
        self.circuit_breaker = self._init_circuit_breaker()
        self.retry_handler = self._init_retry_handler()
        
        # Collection statistics
        self.total_collections = 0
        self.successful_collections = 0
        self.failed_collections = 0
        self.total_execution_time = 0.0
        
        self.logger.info("Base collector initialized", source=self.__class__.__name__)

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

    async def collect_with_protection(self, target: str, **kwargs) -> CollectionResult:
        """
        Collect data with all protection mechanisms enabled.
        This is the main entry point that should be used by external callers.
        """
        start_time = datetime.now()
        correlation_id = self._generate_correlation_id()
        
        try:
            # Publish collection started event
            await self._publish_collection_event(
                EventType.DATA_COLLECTION_STARTED,
                target=target,
                correlation_id=correlation_id
            )
            
            # Check rate limit
            rate_limit_key = f"{self.__class__.__name__}:{target}"
            allowed, rate_limit_info = await self.rate_limiter.is_allowed(rate_limit_key)
            
            if not allowed:
                await self._publish_collection_event(
                    EventType.RATE_LIMIT_EXCEEDED,
                    target=target,
                    correlation_id=correlation_id,
                    rate_limit_info=rate_limit_info
                )
                raise Exception(f"Rate limit exceeded: {rate_limit_info}")
            
            # Execute collection with circuit breaker and retry protection
            result = await self.retry_handler.execute(
                lambda: self.circuit_breaker.call(self._protected_collect, target, **kwargs)
            )
            
            # Update statistics
            execution_time = (datetime.now() - start_time).total_seconds()
            self.total_collections += 1
            self.successful_collections += 1
            self.total_execution_time += execution_time
            
            # Add execution metadata
            result.execution_time = execution_time
            result.retry_count = getattr(result, 'retry_count', 0)
            
            # Publish success event
            await self._publish_collection_event(
                EventType.DATA_COLLECTION_COMPLETED,
                target=target,
                correlation_id=correlation_id,
                result=result
            )
            
            self.logger.info(
                "Data collection completed successfully",
                target=target,
                execution_time=execution_time,
                data_count=len(result.data),
                quality_score=result.quality_score
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.total_collections += 1
            self.failed_collections += 1
            self.total_execution_time += execution_time
            
            # Publish failure event
            await self._publish_collection_event(
                EventType.DATA_COLLECTION_FAILED,
                target=target,
                correlation_id=correlation_id,
                error=str(e),
                execution_time=execution_time
            )
            
            self.logger.error(
                "Data collection failed",
                target=target,
                error=str(e),
                execution_time=execution_time
            )
            
            # Return error result
            return CollectionResult(
                source=self.__class__.__name__,
                data=[],
                metadata={"error": str(e), "correlation_id": correlation_id},
                quality_score=0.0,
                collection_timestamp=datetime.now(),
                errors=[str(e)],
                warnings=[],
                execution_time=execution_time,
                cache_hit=False,
                retry_count=0
            )
    
    async def _protected_collect(self, target: str, **kwargs) -> CollectionResult:
        """Internal collection method with basic protection"""
        try:
            return await self.collect(target, **kwargs)
        except Exception as e:
            self.logger.error(
                "Collection method failed",
                target=target,
                error=str(e)
            )
            raise
    
    def _init_rate_limiter(self) -> RateLimiter:
        """Initialize rate limiter based on config"""
        rate_limit_config = self.config.get('rate_limit', {})
        
        config = RateLimitConfig(
            max_requests=rate_limit_config.get('max_requests', 100),
            window_seconds=rate_limit_config.get('window_seconds', 60),
            burst_size=rate_limit_config.get('burst_size', 10),
            cost_per_request=rate_limit_config.get('cost_per_request', 1)
        )
        
        # Note: In a real implementation, you'd get the Redis client from config
        # For now, we'll create a mock rate limiter
        from .rate_limiter import RateLimiter
        return RateLimiter(None, config)  # Mock Redis client
    
    def _init_circuit_breaker(self) -> CircuitBreaker:
        """Initialize circuit breaker for fault tolerance"""
        circuit_config = self.config.get('circuit_breaker', {})
        
        config = CircuitBreakerConfig(
            failure_threshold=circuit_config.get('failure_threshold', 5),
            recovery_timeout=circuit_config.get('recovery_timeout', 60.0),
            expected_exception=Exception,
            success_threshold=circuit_config.get('success_threshold', 2)
        )
        
        from .circuit_breaker import CircuitBreaker
        return CircuitBreaker(self.__class__.__name__, config)
    
    def _init_retry_handler(self) -> RetryHandler:
        """Initialize retry handler with exponential backoff"""
        retry_config = self.config.get('retry', {})
        
        if retry_config.get('strategy') == 'api_call':
            config = RetryConfigs.api_call()
        elif retry_config.get('strategy') == 'web_scraping':
            config = RetryConfigs.web_scraping()
        else:
            config = RetryConfig(
                max_attempts=retry_config.get('max_attempts', 3),
                base_delay=retry_config.get('base_delay', 1.0),
                max_delay=retry_config.get('max_delay', 60.0),
                jitter=retry_config.get('jitter', True)
            )
        
        from .retry_handler import RetryHandler
        return RetryHandler(config)
    
    async def _publish_collection_event(
        self, 
        event_type: EventType, 
        target: str, 
        correlation_id: str,
        **additional_data
    ):
        """Publish collection-related events"""
        try:
            event = (EventBuilder()
                    .with_type(event_type)
                    .with_priority(EventPriority.NORMAL)
                    .with_source(self.__class__.__name__)
                    .with_data({
                        "target": target,
                        "collector": self.__class__.__name__,
                        **additional_data
                    })
                    .with_metadata({
                        "correlation_id": correlation_id,
                        "timestamp": datetime.now().isoformat()
                    })
                    .with_correlation_id(correlation_id)
                    .build())
            
            await publish_event(event)
            
        except Exception as e:
            self.logger.error(
                "Failed to publish collection event",
                event_type=event_type.value,
                error=str(e)
            )
    
    def _generate_correlation_id(self) -> str:
        """Generate a unique correlation ID for tracking"""
        import uuid
        return str(uuid.uuid4())
    
    def get_collector_stats(self) -> Dict[str, Any]:
        """Get collector performance statistics"""
        return {
            "collector_type": self.__class__.__name__,
            "total_collections": self.total_collections,
            "successful_collections": self.successful_collections,
            "failed_collections": self.failed_collections,
            "success_rate": (
                self.successful_collections / self.total_collections * 100
                if self.total_collections > 0 else 0
            ),
            "total_execution_time": self.total_execution_time,
            "average_execution_time": (
                self.total_execution_time / self.total_collections
                if self.total_collections > 0 else 0
            ),
            "rate_limiter_status": self.rate_limiter.get_status("status_check"),
            "circuit_breaker_status": self.circuit_breaker.get_status(),
            "retry_handler_stats": self.retry_handler.get_stats()
        }
    
    async def cleanup(self):
        """Cleanup resources when collector is no longer needed"""
        self.logger.info("Cleaning up collector", source=self.__class__.__name__)
        # Override in subclasses if needed
