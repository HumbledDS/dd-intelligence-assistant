"""
Circuit breaker implementation for fault tolerance in data collection.
Prevents cascading failures by temporarily stopping requests to failing services.
"""

import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject all requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5      # Number of failures before opening
    recovery_timeout: float = 60.0  # Seconds to wait before half-open
    expected_exception: type = Exception  # Exception type to count as failure
    success_threshold: int = 2      # Successes needed to close circuit

class CircuitBreaker:
    """
    Circuit breaker implementation with configurable failure thresholds
    and automatic recovery mechanisms.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.logger = logger.bind(component="circuit_breaker", name=name)
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_state_change = time.time()
        
        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original function exception
        """
        if not self._can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is {self.state.value}"
            )
        
        self.total_requests += 1
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure(e)
            raise
    
    def _can_execute(self) -> bool:
        """Check if execution is allowed based on current state"""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
            
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if current_time - self.last_failure_time >= self.config.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False
            
        elif self.state == CircuitState.HALF_OPEN:
            return True
            
        return False
    
    async def _on_success(self):
        """Handle successful execution"""
        self.success_count += 1
        self.total_successes += 1
        
        self.logger.debug(
            "Request succeeded",
            success_count=self.success_count,
            failure_count=self.failure_count
        )
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    async def _on_failure(self, exception: Exception):
        """Handle failed execution"""
        # Only count expected exceptions
        if not isinstance(exception, self.config.expected_exception):
            return
            
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = time.time()
        
        self.logger.warning(
            "Request failed",
            failure_count=self.failure_count,
            threshold=self.config.failure_threshold,
            exception=str(exception)
        )
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition circuit to open state"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        
        self.logger.warning(
            "Circuit breaker opened",
            old_state=old_state.value,
            new_state=self.state.value,
            failure_count=self.failure_count
        )
    
    def _transition_to_half_open(self):
        """Transition circuit to half-open state"""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = time.time()
        self.success_count = 0
        
        self.logger.info(
            "Circuit breaker half-open",
            old_state=old_state.value,
            new_state=self.state.value
        )
    
    def _transition_to_closed(self):
        """Transition circuit to closed state"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.failure_count = 0
        self.success_count = 0
        
        self.logger.info(
            "Circuit breaker closed",
            old_state=old_state.value,
            new_state=self.state.value
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        current_time = time.time()
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "uptime": current_time - self.last_state_change,
            "failure_rate": (self.total_failures / self.total_requests * 100) if self.total_requests > 0 else 0
        }
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        self.logger.info("Manual reset of circuit breaker")
        self._transition_to_closed()
    
    def force_open(self):
        """Manually force circuit breaker to open state"""
        self.logger.info("Manual force open of circuit breaker")
        self._transition_to_open()

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Manages multiple circuit breakers for different services"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.logger = logger.bind(component="circuit_breaker_manager")
    
    def add_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Add a new circuit breaker"""
        breaker = CircuitBreaker(name, config)
        self.breakers[name] = breaker
        self.logger.info("Added circuit breaker", name=name, config=config)
        return breaker
    
    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.breakers.get(name)
    
    async def call_with_breaker(
        self, 
        breaker_name: str, 
        func: Callable[..., Awaitable[Any]], 
        *args, 
        **kwargs
    ) -> Any:
        """Execute function with specific circuit breaker"""
        breaker = self.get_breaker(breaker_name)
        if not breaker:
            self.logger.warning("Circuit breaker not found", name=breaker_name)
            # Execute without protection if breaker not found
            return await func(*args, **kwargs)
        
        return await breaker.call(func, *args, **kwargs)
    
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all circuit breakers"""
        return {name: breaker.get_status() for name, breaker in self.breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()
        self.logger.info("Reset all circuit breakers")
