import os
import hashlib
import time
from typing import Dict, Set, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
from config import Config
from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class SecurityMetrics:
    """Security metrics for monitoring bot usage."""
    total_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    blocked_requests: int = 0
    unique_users: Set[str] = field(default_factory=set)
    start_time: float = field(default_factory=time.time)

class SecurityManager:
    """Manages security features including rate limiting and abuse prevention."""
    
    def __init__(self):
        """Initialize the security manager."""
        self.metrics = SecurityMetrics()
        
        # Rate limiting per user
        self.user_request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.user_blocked_until: Dict[str, float] = {}
        
        # Global rate limiting
        self.global_request_history = deque(maxlen=1000)
        
        # Suspicious pattern detection
        self.suspicious_patterns = [
            r'(.)\1{20,}',  # Repeated characters
            r'[^\w\s]{10,}',  # Too many special characters
            r'\b(test|spam|flood)\b.*\1.*\1',  # Repeated spam words
        ]
        
        # Blocked content patterns
        self.blocked_patterns = [
            r'(?i)(hack|crack|exploit|ddos|attack)',
            r'(?i)(password|credit.*card|ssn|social.*security)',
            r'(?i)(illegal|drugs|weapons|bomb)',
        ]
        
        # Configuration
        self.max_requests_per_minute = Config.RATE_LIMIT_REQUESTS
        self.rate_limit_window = Config.RATE_LIMIT_PERIOD
        self.max_question_length = Config.MAX_QUESTION_LENGTH
        self.block_duration = 300  # 5 minutes
        
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            bool: True if request is allowed, False if rate limited
        """
        current_time = time.time()
        
        # Check if user is currently blocked
        if user_id in self.user_blocked_until:
            if current_time < self.user_blocked_until[user_id]:
                logger.warning(f"User {user_id} is blocked until {self.user_blocked_until[user_id]}")
                self.metrics.blocked_requests += 1
                return False
            else:
                # Unblock user
                del self.user_blocked_until[user_id]
        
        # Get user's request history
        user_history = self.user_request_history[user_id]
        
        # Remove old requests outside the window
        cutoff_time = current_time - self.rate_limit_window
        while user_history and user_history[0] < cutoff_time:
            user_history.popleft()
        
        # Check if user exceeds rate limit
        if len(user_history) >= self.max_requests_per_minute:
            logger.warning(f"User {user_id} exceeded rate limit ({len(user_history)} requests)")
            self.metrics.rate_limited_requests += 1
            
            # Block user for repeated violations
            if len(user_history) >= self.max_requests_per_minute * 2:
                self.user_blocked_until[user_id] = current_time + self.block_duration
                logger.warning(f"User {user_id} blocked for {self.block_duration} seconds")
            
            return False
        
        # Add current request to history
        user_history.append(current_time)
        self.global_request_history.append(current_time)
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.unique_users.add(user_id)
        
        return True
    
    def validate_question(self, question: str, user_id: str) -> Optional[str]:
        """Validate a question for security and content policy.
        
        Args:
            question: The question to validate
            user_id: User identifier for logging
            
        Returns:
            Optional[str]: Error message if invalid, None if valid
        """
        try:
            # Length check
            if len(question) > self.max_question_length:
                logger.warning(f"User {user_id} submitted question too long: {len(question)} chars")
                return f"Question too long ({len(question)} chars, max {self.max_question_length})"
            
            # Check for blocked content
            import re
            for pattern in self.blocked_patterns:
                if re.search(pattern, question):
                    logger.warning(f"User {user_id} submitted blocked content: {pattern}")
                    self.metrics.blocked_requests += 1
                    return "Question contains prohibited content"
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if re.search(pattern, question):
                    logger.warning(f"User {user_id} submitted suspicious content: {pattern}")
                    return "Question contains suspicious patterns"
            
            # Check for minimum meaningful content
            meaningful_chars = len(re.sub(r'[^\w]', '', question))
            if meaningful_chars < 3:
                return "Question too short or contains no meaningful content"
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating question: {e}")
            return "Error validating question"
    
    def get_user_id(self, telegram_user_id: int, chat_id: int) -> str:
        """Generate a secure user identifier.
        
        Args:
            telegram_user_id: Telegram user ID
            chat_id: Chat ID where the message was sent
            
        Returns:
            str: Hashed user identifier
        """
        # Create a hash that includes both user and chat for privacy
        identifier = f"{telegram_user_id}:{chat_id}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    def check_global_rate_limit(self) -> bool:
        """Check global rate limiting to prevent system overload.
        
        Returns:
            bool: True if request is allowed, False if globally rate limited
        """
        current_time = time.time()
        cutoff_time = current_time - 60  # 1 minute window
        
        # Remove old requests
        while self.global_request_history and self.global_request_history[0] < cutoff_time:
            self.global_request_history.popleft()
        
        # Check global limit (e.g., 100 requests per minute across all users)
        global_limit = 100
        if len(self.global_request_history) >= global_limit:
            logger.warning(f"Global rate limit exceeded: {len(self.global_request_history)} requests")
            return False
        
        return True
    
    def log_security_event(self, event_type: str, user_id: str, details: Dict):
        """Log security-related events.
        
        Args:
            event_type: Type of security event
            user_id: User identifier
            details: Additional event details
        """
        try:
            log_entry = {
                'event_type': event_type,
                'user_id': user_id,
                'timestamp': time.time(),
                **details
            }
            logger.warning(f"Security event: {log_entry}")
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def get_security_stats(self) -> Dict:
        """Get security statistics.
        
        Returns:
            Dict: Security metrics and statistics
        """
        current_time = time.time()
        uptime = current_time - self.metrics.start_time
        
        return {
            'uptime_seconds': uptime,
            'total_requests': self.metrics.total_requests,
            'failed_requests': self.metrics.failed_requests,
            'rate_limited_requests': self.metrics.rate_limited_requests,
            'blocked_requests': self.metrics.blocked_requests,
            'unique_users': len(self.metrics.unique_users),
            'requests_per_hour': (self.metrics.total_requests / uptime * 3600) if uptime > 0 else 0,
            'currently_blocked_users': len(self.user_blocked_until),
            'active_users_last_hour': len([
                user_id for user_id, history in self.user_request_history.items()
                if history and history[-1] > current_time - 3600
            ])
        }
    
    def cleanup_old_data(self):
        """Clean up old security data to prevent memory leaks."""
        current_time = time.time()
        
        # Remove old blocked users
        expired_blocks = [
            user_id for user_id, block_time in self.user_blocked_until.items()
            if current_time > block_time
        ]
        for user_id in expired_blocks:
            del self.user_blocked_until[user_id]
        
        # Remove inactive user histories (older than 1 hour)
        inactive_users = [
            user_id for user_id, history in self.user_request_history.items()
            if not history or history[-1] < current_time - 3600
        ]
        for user_id in inactive_users:
            del self.user_request_history[user_id]
        
        logger.debug(f"Cleaned up {len(expired_blocks)} expired blocks and {len(inactive_users)} inactive users")

# Global security manager instance
security_manager = SecurityManager()
