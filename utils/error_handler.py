"""
Advanced Error Handler
Professional error handling and recovery
"""

import asyncio
import sys
import traceback
import inspect
from typing import Any, Callable, Dict, Optional, Type
from datetime import datetime
from functools import wraps

from utils.logger import setup_logger
from database.crud import create_log
from database.models import SessionLocal

logger = setup_logger(__name__)

class ErrorHandler:
    """Advanced error handling system"""
    
    @staticmethod
    def handle_exception(
        exception: Exception,
        context: str = "",
        raise_again: bool = False,
        log_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Handle an exception
        
        Args:
            exception: Exception to handle
            context: Context where exception occurred
            raise_again: Whether to re-raise the exception
            log_to_db: Whether to log to database
            
        Returns:
            Error information dictionary
        """
        # Get error information
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()
        
        # Create error info
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": error_message,
            "context": context,
            "stack_trace": stack_trace,
            "handled": True
        }
        
        # Log error
        logger.error(f"Error in {context}: {error_type}: {error_message}")
        logger.debug(f"Stack trace:\n{stack_trace}")
        
        # Log to database if enabled
        if log_to_db:
            ErrorHandler._log_error_to_db(error_info)
        
        # Re-raise if requested
        if raise_again:
            raise exception
        
        return error_info
    
    @staticmethod
    def _log_error_to_db(error_info: Dict[str, Any]):
        """Log error to database"""
        try:
            db = SessionLocal()
            
            # Create log entry
            log_message = (
                f"{error_info['type']}: {error_info['message']} | "
                f"Context: {error_info['context']}"
            )
            
            create_log(
                db,
                level="error",
                module="error_handler",
                message=log_message[:500]  # Limit length
            )
            
            db.commit()
            db.close()
            
        except Exception as db_error:
            logger.error(f"Failed to log error to database: {db_error}")
    
    @staticmethod
    def handle_errors(
        context: str = "",
        raise_again: bool = False,
        log_to_db: bool = True,
        retry_count: int = 0,
        retry_delay: float = 1.0
    ):
        """
        Decorator to handle errors in functions
        
        Args:
            context: Context for error messages
            raise_again: Whether to re-raise exceptions
            log_to_db: Whether to log to database
            retry_count: Number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    for attempt in range(retry_count + 1):
                        try:
                            return await func(*args, **kwargs)
                        except Exception as e:
                            if attempt < retry_count:
                                logger.warning(
                                    f"Retry {attempt + 1}/{retry_count} for {func.__name__} "
                                    f"after error: {str(e)}"
                                )
                                await asyncio.sleep(retry_delay)
                                continue
                            
                            error_context = context or f"async function {func.__name__}"
                            return ErrorHandler.handle_exception(
                                e, error_context, raise_again, log_to_db
                            )
                    return None
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    for attempt in range(retry_count + 1):
                        try:
                            return func(*args, **kwargs)
                        except Exception as e:
                            if attempt < retry_count:
                                logger.warning(
                                    f"Retry {attempt + 1}/{retry_count} for {func.__name__} "
                                    f"after error: {str(e)}"
                                )
                                import time
                                time.sleep(retry_delay)
                                continue
                            
                            error_context = context or f"function {func.__name__}"
                            return ErrorHandler.handle_exception(
                                e, error_context, raise_again, log_to_db
                            )
                    return None
                return sync_wrapper
        return decorator

class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        name: str = "circuit_breaker"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        self.logger = setup_logger(f"CircuitBreaker.{name}")
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker"""
        current_state = self._get_state()
        
        if current_state == "OPEN":
            self.logger.warning(f"Circuit breaker {self.name} is OPEN, rejecting request")
            raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is open")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count if not already zero
            if self.failure_count > 0:
                self.failure_count = 0
                self.state = "CLOSED"
                self.logger.info(f"Circuit breaker {self.name} reset to CLOSED")
            
            return result
            
        except Exception as e:
            # Failure
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            self.logger.warning(
                f"Circuit breaker {self.name} failure {self.failure_count}/"
                f"{self.failure_threshold}: {str(e)}"
            )
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.logger.error(f"Circuit breaker {self.name} tripped to OPEN")
            
            raise e
    
    def _get_state(self) -> str:
        """Get current circuit breaker state"""
        if self.state == "OPEN":
            # Check if recovery timeout has passed
            if self.last_failure_time:
                time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                if time_since_failure >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN")
        
        return self.state
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "recovery_timeout": self.recovery_timeout
        }

class RetryManager:
    """Advanced retry management"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        retry_exceptions: tuple = (Exception,)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_exceptions = retry_exceptions
        
        self.logger = setup_logger("RetryManager")
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt}/{self.max_retries}")
                
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if attempt > 0:
                    self.logger.info(f"Retry successful on attempt {attempt}")
                
                return result
                
            except self.retry_exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.base_delay * (self.backoff_factor ** attempt),
                        self.max_delay
                    )
                    
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
                    continue
                else:
                    self.logger.error(f"All {self.max_retries} retry attempts failed")
                    break
        
        # All retries failed
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Retry execution failed without exception")
    
    def create_retry_decorator(self):
        """Create retry decorator"""
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self.execute_with_retry(func, *args, **kwargs)
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    # For sync functions, run in executor
                    async def async_func():
                        return func(*args, **kwargs)
                    
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(
                        self.execute_with_retry(async_func)
                    )
                return sync_wrapper
        return decorator

class GracefulDegradation:
    """Graceful degradation for non-critical failures"""
    
    def __init__(self, fallback_value: Any = None, log_level: str = "WARNING"):
        self.fallback_value = fallback_value
        self.log_level = log_level
        self.logger = setup_logger("GracefulDegradation")
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with graceful degradation"""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
                
        except Exception as e:
            log_message = f"Graceful degradation: {func.__name__} failed, using fallback: {str(e)}"
            
            if self.log_level == "ERROR":
                self.logger.error(log_message)
            elif self.log_level == "WARNING":
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            return self.fallback_value
    
    def create_decorator(self):
        """Create graceful degradation decorator"""
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self.execute(func, *args, **kwargs)
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    # For sync functions, run in executor
                    async def async_func():
                        return func(*args, **kwargs)
                    
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(
                        self.execute(async_func)
                    )
                return sync_wrapper
        return decorator

# Convenience decorators
def handle_errors(context: str = "", raise_again: bool = False, log_to_db: bool = True):
    """Convenience error handling decorator"""
    return ErrorHandler.handle_errors(context, raise_again, log_to_db)

def async_handle_errors(context: str = "", raise_again: bool = False, log_to_db: bool = True):
    """Async error handling decorator"""
    return ErrorHandler.handle_errors(context, raise_again, log_to_db)

def retry(max_retries: int = 3, base_delay: float = 1.0):
    """Retry decorator"""
    retry_manager = RetryManager(max_retries=max_retries, base_delay=base_delay)
    return retry_manager.create_retry_decorator()

def graceful(fallback_value: Any = None):
    """Graceful degradation decorator"""
    degradation = GracefulDegradation(fallback_value=fallback_value)
    return degradation.create_decorator()

# Custom exceptions
class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open"""
    pass

class ValidationError(Exception):
    """Input validation error"""
    pass

class ConfigurationError(Exception):
    """Configuration error"""
    pass

class DatabaseError(Exception):
    """Database operation error"""
    pass

class NetworkError(Exception):
    """Network operation error"""
    pass

class RateLimitError(Exception):
    """Rate limit exceeded"""
    pass