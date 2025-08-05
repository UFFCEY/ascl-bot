import json
import os
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ChatPreferences:
    """Preferences for a specific chat."""
    chat_id: int
    preferences: List[str]
    created_at: float
    updated_at: float

class PreferenceManager:
    """Manages user preferences for different chats."""
    
    def __init__(self, preferences_file: str = "preferences.json"):
        """Initialize the preference manager.
        
        Args:
            preferences_file: File to store preferences
        """
        self.preferences_file = Path(preferences_file)
        self.chat_preferences: Dict[int, ChatPreferences] = {}
        self.load_preferences()
        
        # Common preference examples for validation
        self.common_preferences = {
            "no emojis", "no emoji", "without emojis", "без эмодзи",
            "short responses", "brief", "concise", "короткие ответы",
            "formal tone", "informal tone", "casual", "формально", "неформально",
            "use slang", "no slang", "сленг", "без сленга",
            "be funny", "serious tone", "шутливо", "серьезно",
            "use english", "use russian", "на английском", "на русском",
            "be polite", "be direct", "вежливо", "прямо"
        }
    
    def set_preferences(self, chat_id: int, preferences_text: str) -> bool:
        """Set preferences for a chat.
        
        Args:
            chat_id: Chat ID to set preferences for
            preferences_text: Comma-separated preferences
            
        Returns:
            bool: True if set successfully
        """
        try:
            # Parse preferences
            preferences = self._parse_preferences(preferences_text)
            
            if not preferences:
                # Clear preferences if empty
                if chat_id in self.chat_preferences:
                    del self.chat_preferences[chat_id]
                    logger.info(f"Cleared preferences for chat {chat_id}")
                else:
                    logger.info(f"No preferences to clear for chat {chat_id}")
            else:
                # Set new preferences
                current_time = time.time()
                
                if chat_id in self.chat_preferences:
                    # Update existing
                    self.chat_preferences[chat_id].preferences = preferences
                    self.chat_preferences[chat_id].updated_at = current_time
                    logger.info(f"Updated preferences for chat {chat_id}: {preferences}")
                else:
                    # Create new
                    self.chat_preferences[chat_id] = ChatPreferences(
                        chat_id=chat_id,
                        preferences=preferences,
                        created_at=current_time,
                        updated_at=current_time
                    )
                    logger.info(f"Set new preferences for chat {chat_id}: {preferences}")
            
            # Save to file
            self.save_preferences()
            return True
            
        except Exception as e:
            logger.error(f"Error setting preferences for chat {chat_id}: {e}")
            return False
    
    def get_preferences(self, chat_id: int) -> List[str]:
        """Get preferences for a chat.
        
        Args:
            chat_id: Chat ID to get preferences for
            
        Returns:
            List[str]: List of preferences
        """
        chat_prefs = self.chat_preferences.get(chat_id)
        return chat_prefs.preferences if chat_prefs else []
    
    def get_preferences_text(self, chat_id: int) -> str:
        """Get preferences as formatted text for AI prompts.
        
        Args:
            chat_id: Chat ID to get preferences for
            
        Returns:
            str: Formatted preferences text
        """
        preferences = self.get_preferences(chat_id)
        if not preferences:
            return ""
        
        return f"Additional instructions: {', '.join(preferences)}"
    
    def has_preferences(self, chat_id: int) -> bool:
        """Check if a chat has any preferences set.
        
        Args:
            chat_id: Chat ID to check
            
        Returns:
            bool: True if preferences exist
        """
        return chat_id in self.chat_preferences and bool(self.chat_preferences[chat_id].preferences)
    
    def _parse_preferences(self, preferences_text: str) -> List[str]:
        """Parse preferences from text.
        
        Args:
            preferences_text: Raw preferences text
            
        Returns:
            List[str]: Parsed preferences
        """
        if not preferences_text or not preferences_text.strip():
            return []
        
        # Split by comma and clean up
        preferences = []
        for pref in preferences_text.split(','):
            cleaned = pref.strip().lower()
            if cleaned:
                preferences.append(cleaned)
        
        return preferences
    
    def load_preferences(self):
        """Load preferences from file."""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for chat_id_str, pref_data in data.items():
                    chat_id = int(chat_id_str)
                    self.chat_preferences[chat_id] = ChatPreferences(
                        chat_id=chat_id,
                        preferences=pref_data['preferences'],
                        created_at=pref_data.get('created_at', time.time()),
                        updated_at=pref_data.get('updated_at', time.time())
                    )
                
                logger.info(f"Loaded preferences for {len(self.chat_preferences)} chats")
            else:
                logger.info("No preferences file found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
            self.chat_preferences = {}
    
    def save_preferences(self):
        """Save preferences to file."""
        try:
            data = {}
            for chat_id, prefs in self.chat_preferences.items():
                data[str(chat_id)] = asdict(prefs)
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Preferences saved to file")
            
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
    
    def get_all_preferences(self) -> Dict[int, List[str]]:
        """Get all preferences for all chats.
        
        Returns:
            Dict[int, List[str]]: All preferences by chat ID
        """
        return {chat_id: prefs.preferences for chat_id, prefs in self.chat_preferences.items()}
    
    def cleanup_old_preferences(self, days: int = 30):
        """Clean up old unused preferences.
        
        Args:
            days: Remove preferences older than this many days
        """
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            old_chats = [
                chat_id for chat_id, prefs in self.chat_preferences.items()
                if prefs.updated_at < cutoff_time
            ]
            
            for chat_id in old_chats:
                del self.chat_preferences[chat_id]
            
            if old_chats:
                logger.info(f"Cleaned up preferences for {len(old_chats)} old chats")
                self.save_preferences()
                
        except Exception as e:
            logger.error(f"Error cleaning up preferences: {e}")

# Global preference manager instance
preference_manager = PreferenceManager()
