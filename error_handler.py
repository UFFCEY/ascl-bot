import asyncio
import traceback
from typing import Optional, Callable, Any, Dict
from functools import wraps
from telethon.errors import (
    FloodWaitError,
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    ApiIdInvalidError,
    RPCError
)
import openai
from logger import setup_logger

logger = setup_logger(__name__)

class ErrorHandler:
    """Centralized error handling and recovery mechanisms."""
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_counts = {}
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
    
    def with_retry(self, max_retries: Optional[int] = None, delay: Optional[float] = None):
        """Decorator for automatic retry with exponential backoff.
        
        Args:
            max_retries: Maximum number of retries (default: 3)
            delay: Base delay between retries (default: 1.0)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                retries = max_retries or self.max_retries
                current_delay = delay or self.base_delay
                
                for attempt in range(retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == retries:
                            logger.error(f"Function {func.__name__} failed after {retries} retries: {e}")
                            raise
                        
                        if self._should_retry(e):
                            wait_time = min(current_delay * (2 ** attempt), self.max_delay)
                            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"Non-retryable error in {func.__name__}: {e}")
                            raise
                
            return wrapper
        return decorator
    
    def _should_retry(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry.
        
        Args:
            error: The exception that occurred
            
        Returns:
            bool: True if should retry, False otherwise
        """
        # Network-related errors that are worth retrying
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            openai.APITimeoutError,
            openai.APIConnectionError,
        )
        
        # Don't retry these errors
        non_retryable_errors = (
            ApiIdInvalidError,
            PhoneCodeInvalidError,
            SessionPasswordNeededError,
            openai.AuthenticationError,
            openai.PermissionDeniedError,
        )
        
        if isinstance(error, non_retryable_errors):
            return False
        
        if isinstance(error, retryable_errors):
            return True
        
        if isinstance(error, FloodWaitError):
            # Don't retry flood wait errors automatically
            return False
        
        if isinstance(error, openai.RateLimitError):
            # Don't retry rate limit errors automatically
            return False
        
        # For unknown errors, be conservative and don't retry
        return False
    
    async def handle_telegram_error(self, error: Exception, context: str = "") -> bool:
        """Handle Telegram-specific errors.
        
        Args:
            error: The Telegram error
            context: Additional context about where the error occurred
            
        Returns:
            bool: True if error was handled and operation can continue, False otherwise
        """
        try:
            if isinstance(error, FloodWaitError):
                wait_time = error.seconds
                logger.warning(f"Flood wait error: waiting {wait_time} seconds. Context: {context}")
                
                if wait_time > 300:  # Don't wait more than 5 minutes
                    logger.error(f"Flood wait too long ({wait_time}s), aborting")
                    return False
                
                await asyncio.sleep(wait_time)
                return True
            
            elif isinstance(error, SessionPasswordNeededError):
                logger.error("Two-factor authentication is enabled. Please disable it or provide password.")
                return False
            
            elif isinstance(error, PhoneCodeInvalidError):
                logger.error("Invalid phone code provided during authentication")
                return False
            
            elif isinstance(error, ApiIdInvalidError):
                logger.error("Invalid API ID or hash. Please check your credentials.")
                return False
            
            elif isinstance(error, (ConnectionError, OSError)):
                logger.warning(f"Network error: {error}. Context: {context}")
                return True  # Can be retried
            
            elif isinstance(error, RPCError):
                logger.error(f"Telegram RPC error: {error}. Context: {context}")
                return False
            
            else:
                logger.error(f"Unhandled Telegram error: {error}. Context: {context}")
                return False
                
        except Exception as e:
            logger.error(f"Error in Telegram error handler: {e}")
            return False
    
    async def handle_ai_error(self, error: Exception, context: str = "") -> Optional[str]:
        """Handle AI service errors and provide user-friendly messages.
        
        Args:
            error: The AI service error
            context: Additional context about where the error occurred
            
        Returns:
            Optional[str]: User-friendly error message, None if error is not recoverable
        """
        try:
            if isinstance(error, openai.RateLimitError):
                logger.warning(f"AI rate limit exceeded. Context: {context}")
                return "⏱️ AI service is temporarily busy. Please try again in a few minutes."
            
            elif isinstance(error, openai.APITimeoutError):
                logger.warning(f"AI request timed out. Context: {context}")
                return "⏰ AI response took too long. Please try a shorter question."
            
            elif isinstance(error, openai.APIConnectionError):
                logger.warning(f"AI connection error. Context: {context}")
                return "🔌 Connection to AI service failed. Please try again."
            
            elif isinstance(error, openai.AuthenticationError):
                logger.error(f"AI authentication failed. Context: {context}")
                return "🔑 AI service authentication failed. Please contact administrator."
            
            elif isinstance(error, openai.PermissionDeniedError):
                logger.error(f"AI permission denied. Context: {context}")
                return "🚫 Access to AI service denied. Please contact administrator."
            
            elif isinstance(error, openai.BadRequestError):
                logger.warning(f"AI bad request: {error}. Context: {context}")
                return "❌ Invalid request to AI service. Please try rephrasing your question."
            
            else:
                logger.error(f"Unhandled AI error: {error}. Context: {context}")
                return "🤖 AI service encountered an unexpected error. Please try again."
                
        except Exception as e:
            logger.error(f"Error in AI error handler: {e}")
            return "❌ An unexpected error occurred."
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """Log an error with detailed context information.
        
        Args:
            error: The exception that occurred
            context: Context dictionary with relevant information
        """
        try:
            error_info = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                **context
            }
            
            logger.error(f"Error occurred: {error_info}")
            
            # Track error frequency
            error_key = f"{type(error).__name__}:{str(error)[:100]}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Log warning if error is frequent
            if self.error_counts[error_key] > 5:
                logger.warning(f"Frequent error detected: {error_key} (count: {self.error_counts[error_key]})")
                
        except Exception as e:
            logger.error(f"Error in error logging: {e}")
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error frequency statistics.
        
        Returns:
            Dict[str, int]: Error counts by type
        """
        return self.error_counts.copy()

# Global error handler instance
error_handler = ErrorHandler()
