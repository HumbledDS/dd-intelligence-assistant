"""
Retry handler implementation with exponential backoff and jitter.
Provides resilient retry mechanisms for data collection operations.
"""

import asyncio
import random
import time
from typing import Dict, Any, Optional, Callable, Awaitable, List, Type
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

class RetryStrategy(Enum):
    """Retry strategies"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"
    FIBONACCI = "fibonacci"

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0   # Maximum delay in seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True       # Add random jitter to delays
    backoff_factor: float = 2.0  # Multiplier for exponential backoff
    retryable_exceptions: List[Type[Exception]] = None
    on_retry: Optional[Callable[[int, Exception, float], None]] = None

class RetryHandler:
    """
    Retry handler with configurable strategies and exponential backoff.
    Supports different retry strategies and automatic exception handling.
    """
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logger.bind(component="retry_handler")
        
        # Set default retryable exceptions if none provided
        if self.config.retryable_exceptions is None:
            self.config.retryable_exceptions = [
                ConnectionError,
                TimeoutError,
                OSError,
                Exception  # Generic fallback
            ]
    
    async def execute(
        self, 
        func: Callable[..., Awaitable[Any]], 
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception after all retries exhausted
        """
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 1:
                    self.logger.info(
                        "Function succeeded on retry",
                        attempt=attempt,
                        function=func.__name__
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if exception is retryable
                if not self._is_retryable(e):
                    self.logger.warning(
                        "Non-retryable exception, not retrying",
                        exception=str(e),
                        attempt=attempt
                    )
                    raise e
                
                # Check if we've exhausted retries
                if attempt >= self.config.max_attempts:
                    self.logger.error(
                        "Max retries exhausted",
                        max_attempts=self.config.max_attempts,
                        last_exception=str(last_exception),
                        function=func.__name__
                    )
                    raise last_exception
                
                # Calculate delay for next retry
                delay = self._calculate_delay(attempt)
                
                self.logger.warning(
                    "Function failed, retrying",
                    attempt=attempt,
                    max_attempts=self.config.max_attempts,
                    exception=str(e),
                    delay=delay,
                    function=func.__name__
                )
                
                # Call on_retry callback if provided
                if self.config.on_retry:
                    try:
                        self.config.on_retry(attempt, e, delay)
                    except Exception as callback_error:
                        self.logger.error(
                            "Error in on_retry callback",
                            error=str(callback_error)
                        )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception
    
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt"""
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_factor ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * attempt
        elif self.config.strategy == RetryStrategy.CONSTANT:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self.config.base_delay * self._fibonacci(attempt)
        else:
            delay = self.config.base_delay
        
        # Add jitter if enabled
        if self.config.jitter:
            jitter_factor = random.uniform(0.8, 1.2)
            delay *= jitter_factor
        
        # Cap delay at maximum
        return min(delay, self.config.max_delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calculate fibonacci number for retry delay"""
        if n <= 1:
            return n
        return self._fibonacci(n - 1) + self._fibonacci(n - 2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry handler statistics"""
        return {
            "max_attempts": self.config.max_attempts,
            "base_delay": self.config.base_delay,
            "max_delay": self.config.max_delay,
            "strategy": self.config.strategy.value,
            "jitter": self.config.jitter,
            "backoff_factor": self.config.backoff_factor,
            "retryable_exceptions": [exc.__name__ for exc in self.config.retryable_exceptions]
        }

class RetryManager:
    """Manages multiple retry handlers for different operations"""
    
    def __init__(self):
        self.handlers: Dict[str, RetryHandler] = {}
        self.logger = logger.bind(component="retry_manager")
    
    def add_handler(self, name: str, config: RetryConfig) -> RetryHandler:
        """Add a new retry handler"""
        handler = RetryHandler(config)
        self.handlers[name] = handler
        self.logger.info("Added retry handler", name=name, config=config)
        return handler
    
    def get_handler(self, name: str) -> Optional[RetryHandler]:
        """Get retry handler by name"""
        return self.handlers.get(name)
    
    async def execute_with_retry(
        self, 
        handler_name: str, 
        func: Callable[..., Awaitable[Any]], 
        *args, 
        **kwargs
    ) -> Any:
        """Execute function with specific retry handler"""
        handler = self.get_handler(handler_name)
        if not handler:
            self.logger.warning("Retry handler not found", name=handler_name)
            # Execute without retry if handler not found
            return await func(*args, **kwargs)
        
        return await handler.execute(func, *args, **kwargs)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all retry handlers"""
        return {name: handler.get_stats() for name, handler in self.handlers.items()}

# Predefined retry configurations
class RetryConfigs:
    """Common retry configurations for different scenarios"""
    
    @staticmethod
    def api_call() -> RetryConfig:
        """Configuration for API calls"""
        return RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True,
            retryable_exceptions=[ConnectionError, TimeoutError, OSError]
        )
    
    @staticmethod
    def file_operation() -> RetryConfig:
        """Configuration for file operations"""
        return RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=10.0,
            strategy=RetryStrategy.LINEAR,
            jitter=False,
            retryable_exceptions=[OSError, PermissionError]
        )
    
    @staticmethod
    def database_operation() -> RetryConfig:
        """Configuration for database operations"""
        return RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=60.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True,
            retryable_exceptions=[ConnectionError, TimeoutError]
        )
    
    @staticmethod
    def web_scraping() -> RetryConfig:
        """Configuration for web scraping operations"""
        return RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True,
            retryable_exceptions=[ConnectionError, TimeoutError, OSError]
        )
