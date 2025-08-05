import asyncio
import time
from typing import Dict, Set, Optional
from dataclasses import dataclass
from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class AutoResponseState:
    """State information for auto-response in a chat."""
    chat_id: int
    enabled: bool
    enabled_at: float
    last_response_time: float
    response_count: int
    skip_count: int = 0  # Number of times AI decided to skip

class AutoResponseManager:
    """Manages automatic response state for different chats."""
    
    def __init__(self):
        """Initialize the auto-response manager."""
        self.auto_response_chats: Dict[int, AutoResponseState] = {}
        self.cooldown_period = 30  # Minimum seconds between auto-responses
        self.max_responses_per_hour = 10  # Limit auto-responses per chat
        
    def enable_auto_response(self, chat_id: int) -> bool:
        """Enable automatic responses for a chat.
        
        Args:
            chat_id: Chat ID to enable auto-response for
            
        Returns:
            bool: True if enabled successfully
        """
        try:
            current_time = time.time()
            
            if chat_id in self.auto_response_chats:
                # Update existing state
                state = self.auto_response_chats[chat_id]
                state.enabled = True
                state.enabled_at = current_time
                logger.info(f"Re-enabled auto-response for chat {chat_id}")
            else:
                # Create new state
                self.auto_response_chats[chat_id] = AutoResponseState(
                    chat_id=chat_id,
                    enabled=True,
                    enabled_at=current_time,
                    last_response_time=0,
                    response_count=0,
                    skip_count=0
                )
                logger.info(f"Enabled auto-response for chat {chat_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error enabling auto-response for chat {chat_id}: {e}")
            return False
    
    def disable_auto_response(self, chat_id: int) -> bool:
        """Disable automatic responses for a chat.
        
        Args:
            chat_id: Chat ID to disable auto-response for
            
        Returns:
            bool: True if disabled successfully
        """
        try:
            if chat_id in self.auto_response_chats:
                self.auto_response_chats[chat_id].enabled = False
                logger.info(f"Disabled auto-response for chat {chat_id}")
                return True
            else:
                logger.warning(f"Auto-response was not enabled for chat {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error disabling auto-response for chat {chat_id}: {e}")
            return False
    
    def is_auto_response_enabled(self, chat_id: int) -> bool:
        """Check if auto-response is enabled for a chat.
        
        Args:
            chat_id: Chat ID to check
            
        Returns:
            bool: True if auto-response is enabled
        """
        state = self.auto_response_chats.get(chat_id)
        return state is not None and state.enabled
    
    def should_auto_respond(self, chat_id: int, sender_id: int, owner_id: int) -> bool:
        """Check if bot should automatically respond to a message.
        
        Args:
            chat_id: Chat ID where message was sent
            sender_id: ID of message sender
            owner_id: ID of bot owner
            
        Returns:
            bool: True if should auto-respond
        """
        try:
            # Don't respond to owner's own messages
            if sender_id == owner_id:
                return False
            
            # Check if auto-response is enabled for this chat
            if not self.is_auto_response_enabled(chat_id):
                return False
            
            state = self.auto_response_chats[chat_id]
            current_time = time.time()
            
            # Check cooldown period
            if current_time - state.last_response_time < self.cooldown_period:
                logger.debug(f"Auto-response cooldown active for chat {chat_id}")
                return False
            
            # Check hourly rate limit
            hour_ago = current_time - 3600
            if state.enabled_at > hour_ago:
                # Count responses since enabled (if less than an hour ago)
                if state.response_count >= self.max_responses_per_hour:
                    logger.warning(f"Auto-response rate limit reached for chat {chat_id}")
                    return False
            else:
                # Reset counter if more than an hour has passed
                state.response_count = 0
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking auto-response for chat {chat_id}: {e}")
            return False
    
    def record_auto_response(self, chat_id: int) -> bool:
        """Record that an auto-response was sent.
        
        Args:
            chat_id: Chat ID where response was sent
            
        Returns:
            bool: True if recorded successfully
        """
        try:
            if chat_id in self.auto_response_chats:
                state = self.auto_response_chats[chat_id]
                state.last_response_time = time.time()
                state.response_count += 1
                logger.debug(f"Recorded auto-response for chat {chat_id} (count: {state.response_count})")
                return True
            else:
                logger.warning(f"Tried to record auto-response for unknown chat {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error recording auto-response for chat {chat_id}: {e}")
            return False

    def record_skip(self, chat_id: int) -> bool:
        """Record that an auto-response was skipped.

        Args:
            chat_id: Chat ID where response was skipped

        Returns:
            bool: True if recorded successfully
        """
        try:
            if chat_id in self.auto_response_chats:
                state = self.auto_response_chats[chat_id]
                state.skip_count += 1
                logger.debug(f"Recorded skip for chat {chat_id} (total skips: {state.skip_count})")
                return True
            else:
                logger.warning(f"Tried to record skip for unknown chat {chat_id}")
                return False

        except Exception as e:
            logger.error(f"Error recording skip for chat {chat_id}: {e}")
            return False
    
    def get_auto_response_status(self, chat_id: int) -> Optional[Dict]:
        """Get auto-response status for a chat.
        
        Args:
            chat_id: Chat ID to get status for
            
        Returns:
            Optional[Dict]: Status information or None
        """
        try:
            state = self.auto_response_chats.get(chat_id)
            if not state:
                return None
            
            current_time = time.time()
            return {
                'enabled': state.enabled,
                'enabled_duration': current_time - state.enabled_at,
                'last_response_ago': current_time - state.last_response_time if state.last_response_time > 0 else None,
                'response_count': state.response_count,
                'skip_count': state.skip_count,
                'response_rate': state.response_count / (state.response_count + state.skip_count) if (state.response_count + state.skip_count) > 0 else 0,
                'cooldown_remaining': max(0, self.cooldown_period - (current_time - state.last_response_time)) if state.last_response_time > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting auto-response status for chat {chat_id}: {e}")
            return None
    
    def get_enabled_chats(self) -> Set[int]:
        """Get set of chat IDs with auto-response enabled.
        
        Returns:
            Set[int]: Set of chat IDs
        """
        return {chat_id for chat_id, state in self.auto_response_chats.items() if state.enabled}
    
    def cleanup_old_states(self):
        """Clean up old auto-response states to prevent memory leaks."""
        try:
            current_time = time.time()
            week_ago = current_time - (7 * 24 * 3600)  # 7 days
            
            old_chats = [
                chat_id for chat_id, state in self.auto_response_chats.items()
                if not state.enabled and state.enabled_at < week_ago
            ]
            
            for chat_id in old_chats:
                del self.auto_response_chats[chat_id]
            
            if old_chats:
                logger.info(f"Cleaned up {len(old_chats)} old auto-response states")
                
        except Exception as e:
            logger.error(f"Error cleaning up auto-response states: {e}")

# Global auto-response manager instance
auto_response_manager = AutoResponseManager()
