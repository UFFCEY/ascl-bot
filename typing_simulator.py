import asyncio
import random
import re
from typing import Optional
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction
from config import Config
from logger import setup_logger

logger = setup_logger(__name__)

class TypingSimulator:
    """Simulates realistic human typing behavior for Telegram messages."""
    
    def __init__(self):
        """Initialize the typing simulator."""
        self.wpm = Config.TYPING_SPEED_WPM
        self.min_delay = Config.TYPING_MIN_DELAY
        self.max_delay = Config.TYPING_MAX_DELAY
        self.variation = Config.TYPING_VARIATION
        self.pause_chance = Config.TYPING_PAUSE_CHANCE
        
    def calculate_typing_time(self, text: str) -> float:
        """Calculate realistic typing time for a given text.
        
        Args:
            text: The text that will be "typed"
            
        Returns:
            float: Typing time in seconds
        """
        try:
            # Count words (approximate)
            words = len(re.findall(r'\b\w+\b', text))
            
            # Base typing time (words per minute to seconds)
            base_time = (words / self.wpm) * 60
            
            # Add variation to simulate human inconsistency
            variation_factor = 1 + random.uniform(-self.variation, self.variation)
            typing_time = base_time * variation_factor
            
            # Add thinking pauses for longer messages
            if words > 10 and random.random() < self.pause_chance:
                thinking_pause = random.uniform(1, 3)
                typing_time += thinking_pause
                logger.debug(f"Added thinking pause: {thinking_pause:.1f}s")
            
            # Ensure within reasonable bounds
            typing_time = max(self.min_delay, min(typing_time, self.max_delay))
            
            logger.debug(f"Calculated typing time: {typing_time:.1f}s for {words} words")
            return typing_time
            
        except Exception as e:
            logger.warning(f"Error calculating typing time: {e}")
            return self.min_delay
    
    async def simulate_typing(self, client, chat_entity, text: str) -> None:
        """Simulate typing animation and delay for a message.
        
        Args:
            client: Telegram client instance
            chat_entity: Chat where typing should be shown
            text: Text that will be sent (for timing calculation)
        """
        try:
            typing_time = self.calculate_typing_time(text)
            
            # Start typing animation
            await client(SetTypingRequest(
                peer=chat_entity,
                action=SendMessageTypingAction()
            ))
            logger.debug("Started typing animation")
            
            # Simulate typing with periodic animation updates
            elapsed = 0
            update_interval = 3  # Update typing animation every 3 seconds
            
            while elapsed < typing_time:
                sleep_time = min(update_interval, typing_time - elapsed)
                await asyncio.sleep(sleep_time)
                elapsed += sleep_time
                
                # Refresh typing animation if still typing
                if elapsed < typing_time:
                    await client(SetTypingRequest(
                        peer=chat_entity,
                        action=SendMessageTypingAction()
                    ))
                    logger.debug("Refreshed typing animation")
            
            logger.debug(f"Completed typing simulation ({typing_time:.1f}s)")
            
        except Exception as e:
            logger.warning(f"Error during typing simulation: {e}")
            # Fallback to minimum delay without animation
            await asyncio.sleep(self.min_delay)
    
    async def simulate_quick_typing(self, client, chat_entity, duration: float = 2.0) -> None:
        """Simulate quick typing for short messages or info messages.
        
        Args:
            client: Telegram client instance
            chat_entity: Chat where typing should be shown
            duration: Typing duration in seconds
        """
        try:
            # Start typing animation
            await client(SetTypingRequest(
                peer=chat_entity,
                action=SendMessageTypingAction()
            ))
            logger.debug(f"Started quick typing animation ({duration}s)")
            
            # Wait for the specified duration
            await asyncio.sleep(duration)
            
            logger.debug("Completed quick typing simulation")
            
        except Exception as e:
            logger.warning(f"Error during quick typing simulation: {e}")
            # Fallback to simple delay
            await asyncio.sleep(min(duration, 1.0))
    
    def get_typing_stats(self, text: str) -> dict:
        """Get typing statistics for a text.
        
        Args:
            text: Text to analyze
            
        Returns:
            dict: Typing statistics
        """
        try:
            words = len(re.findall(r'\b\w+\b', text))
            chars = len(text)
            typing_time = self.calculate_typing_time(text)
            
            return {
                'words': words,
                'characters': chars,
                'estimated_time': typing_time,
                'wpm': self.wpm,
                'effective_wpm': (words / typing_time * 60) if typing_time > 0 else 0
            }
            
        except Exception as e:
            logger.warning(f"Error getting typing stats: {e}")
            return {
                'words': 0,
                'characters': len(text) if text else 0,
                'estimated_time': self.min_delay,
                'wpm': self.wpm,
                'effective_wpm': 0
            }

# Global typing simulator instance
typing_simulator = TypingSimulator()
