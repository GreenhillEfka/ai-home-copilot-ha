"""
Central Error Handler with comprehensive error management.

Features:
- Error classification (Recoverable vs Fatal)
- Retry logic with exponential backoff
- Circuit breaker pattern
- Fallback strategies
- Error tracking and analytics
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Type, Union
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorClassification(Enum):
    """Classify errors by severity and recoverability."""
    
    # Recoverable errors - can retry
    NETWORK_TIMEOUT = "network_timeout"
    RATE_LIMIT = "rate_limit"
    TEMPORARY_UNAVAILABLE = "temp_unavailable"
    CONNECTION_LOST = "connection_lost"
    
    # Potentially recoverable - may need fallback
    VALIDATION_ERROR = "validation_error"
    CONFIG_ERROR = "config_error"
    DEPENDENCY_FAILURE = "dependency_failure"
    
    # Fatal errors - should not retry
    CRITICAL_FAILURE = "critical_failure"
    DATA_CORRUPTION = "data_corruption"
    AUTHENTICATION_FAILED = "auth_failed"
    PERMISSION_DENIED = "permission_denied"
    INVALID_STATE = "invalid_state"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    
    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # seconds
    half_open_max_calls: int = 3


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ErrorContext:
    """Context information about an error."""
    
    error_type: str
    classification: ErrorClassification
    message: str
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    component: str = ""
    metadata: dict = field(default_factory=dict)
    original_exception: Optional[Exception] = None


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation.
    
    Prevents cascading failures by failing fast when a service is down.
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if not await self._can_execute():
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time is None:
                return False
            
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    async def _on_success(self):
        """Handle successful execution."""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0
    
    async def _on_failure(self):
        """Handle failed execution."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class FallbackStrategy:
    """
    Fallback Strategy Pattern.
    
    Provides alternative execution paths when primary fails.
    """
    
    def __init__(self):
        self.fallbacks: list[Callable] = []
    
    def add_fallback(self, func: Callable, priority: int = 0):
        """Add a fallback function."""
        self.fallbacks.append((priority, func))
        self.fallbacks.sort(key=lambda x: x[0])
    
    async def execute(self, primary: Callable, *args, **kwargs) -> Any:
        """Execute primary, fall back on failure."""
        last_error = None
        
        # Try primary
        try:
            return await primary(*args, **kwargs) if asyncio.iscoroutinefunction(primary) else primary(*args, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(f"Primary execution failed: {e}")
        
        # Try fallbacks in priority order
        for _, fallback in self.fallbacks:
            try:
                logger.info(f"Executing fallback: {fallback.__name__}")
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Fallback failed: {e}")
        
        # All failed
        if last_error:
            raise last_error
        raise RuntimeError("All execution paths failed")


class ErrorHandler:
    """
    Central Error Handler.
    
    Provides unified error handling with classification, retry, and circuit breaker.
    """
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        component: str = "default"
    ):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)
        self.component = component
        self.error_history: list[ErrorContext] = []
        self._error_handlers: dict[Type[Exception], Callable] = {}
    
    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """Register a custom handler for specific exception types."""
        self._error_handlers[exception_type] = handler
    
    def classify_error(self, exception: Exception) -> ErrorClassification:
        """Classify an exception by type and context."""
        error_str = str(exception).lower()
        
        # Network-related (recoverable)
        if any(x in error_str for x in ["timeout", "timed out"]):
            return ErrorClassification.NETWORK_TIMEOUT
        if "rate limit" in error_str or "429" in error_str:
            return ErrorClassification.RATE_LIMIT
        if "connection" in error_str and ("lost" in error_str or "refused" in error_str):
            return ErrorClassification.CONNECTION_LOST
        
        # Auth/Permission (fatal)
        if "auth" in error_str or "unauthorized" in error_str or "401" in error_str:
            return ErrorClassification.AUTHENTICATION_FAILED
        if "permission" in error_str or "forbidden" in error_str or "403" in error_str:
            return ErrorClassification.PERMISSION_DENIED
        
        # Validation/Config (potentially recoverable)
        if "validation" in error_str or "invalid" in error_str:
            return ErrorClassification.VALIDATION_ERROR
        if "config" in error_str or "configuration" in error_str:
            return ErrorClassification.CONFIG_ERROR
        
        # Default to critical
        return ErrorClassification.CRITICAL_FAILURE
    
    def is_retryable(self, exception: Exception) -> bool:
        """Determine if an error is retryable."""
        classification = self.classify_error(exception)
        
        # Retryable classifications
        retryable = {
            ErrorClassification.NETWORK_TIMEOUT,
            ErrorClassification.RATE_LIMIT,
            ErrorClassification.TEMPORARY_UNAVAILABLE,
            ErrorClassification.CONNECTION_LOST,
        }
        
        # Check if exception type matches retryable config
        if isinstance(exception, self.retry_config.retryable_exceptions):
            return classification in retryable
        
        return classification in retryable
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with exponential backoff retry."""
        last_exception = None
        delay = self.retry_config.base_delay
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.is_retryable(e):
                    logger.error(f"Non-retryable error: {e}")
                    raise
                
                if attempt >= self.retry_config.max_retries:
                    logger.error(f"Max retries ({self.retry_config.max_retries}) exceeded")
                    raise
                
                # Log retry attempt
                logger.warning(
                    f"Retry {attempt + 1}/{self.retry_config.max_retries} after {delay:.2f}s: {e}"
                )
                
                # Wait with exponential backoff
                await asyncio.sleep(delay)
                
                # Calculate next delay with exponential backoff and jitter
                if self.retry_config.jitter:
                    import random
                    jitter = random.uniform(0, delay * 0.1)
                else:
                    jitter = 0
                
                delay = min(
                    delay * self.retry_config.exponential_base + jitter,
                    self.retry_config.max_delay
                )
        
        if last_exception:
            raise last_exception
    
    async def execute_with_circuit_breaker(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection."""
        return await self.circuit_breaker.call(func, *args, **kwargs)
    
    def record_error(
        self,
        exception: Exception,
        context: Optional[dict] = None
    ) -> ErrorContext:
        """Record an error for tracking and analytics."""
        error_context = ErrorContext(
            error_type=type(exception).__name__,
            classification=self.classify_error(exception),
            message=str(exception),
            component=self.component,
            metadata=context or {},
            original_exception=exception
        )
        
        self.error_history.append(error_context)
        
        # Keep history bounded
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
        
        return error_context
    
    def get_error_summary(self) -> dict:
        """Get summary of recent errors."""
        if not self.error_history:
            return {"total": 0, "by_classification": {}, "recent": []}
        
        by_class = {}
        for error in self.error_history[-100:]:
            key = error.classification.value
            by_class[key] = by_class.get(key, 0) + 1
        
        return {
            "total": len(self.error_history),
            "by_classification": by_class,
            "recent": [
                {
                    "type": e.error_type,
                    "classification": e.classification.value,
                    "message": e.message,
                    "timestamp": e.timestamp
                }
                for e in self.error_history[-10:]
            ]
        }
    
    def handle(self, exception: Exception, context: Optional[dict] = None):
        """
        Handle an exception using registered handlers.
        
        Falls back to default handling if no specific handler registered.
        """
        # Record the error
        error_context = self.record_error(exception, context)
        
        # Check for specific handler
        for exc_type, handler in self._error_handlers.items():
            if isinstance(exception, exc_type):
                try:
                    return handler(exception, error_context)
                except Exception as e:
                    logger.error(f"Error handler failed: {e}")
        
        # Default handling based on classification
        if error_context.classification in {
            ErrorClassification.AUTHENTICATION_FAILED,
            ErrorClassification.PERMISSION_DENIED,
            ErrorClassification.DATA_CORRUPTION,
            ErrorClassification.CRITICAL_FAILURE
        }:
            logger.critical(f"Fatal error in {self.component}: {exception}")
            raise
        else:
            logger.warning(f"Error in {self.component}: {exception}")
            raise


def with_error_handler(
    error_handler: Optional[ErrorHandler] = None,
    retry: bool = True,
    circuit_breaker: bool = True
):
    """
    Decorator to add error handling to async functions.
    
    Usage:
        @with_error_handler(retry=True, circuit_breaker=True)
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get or create error handler
            handler = error_handler or ErrorHandler(component=func.__name__)
            
            # Wrap function
            async def execute():
                return await func(*args, **kwargs)
            
            # Apply circuit breaker
            if circuit_breaker:
                execute = lambda: handler.execute_with_circuit_breaker(func, *args, **kwargs)
            
            # Apply retry
            if retry:
                return await handler.execute_with_retry(execute)
            else:
                return await execute()
        
        return wrapper
    return decorator
