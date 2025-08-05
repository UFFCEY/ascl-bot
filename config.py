import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Telegram AI bot."""
    
    # Telegram API credentials
    TELEGRAM_API_ID: int = int(os.getenv('TELEGRAM_API_ID', 0))
    TELEGRAM_API_HASH: str = os.getenv('TELEGRAM_API_HASH', '')
    TELEGRAM_PHONE: str = os.getenv('TELEGRAM_PHONE', '')
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Bot settings
    BOT_COMMAND_PREFIX: str = os.getenv('BOT_COMMAND_PREFIX', '.ascl')
    BOT_ANSWER_PREFIX: str = os.getenv('BOT_ANSWER_PREFIX', '.ans')
    BOT_AUTO_ANSWER_PREFIX: str = os.getenv('BOT_AUTO_ANSWER_PREFIX', '.aans')
    BOT_MANUAL_ANSWER_PREFIX: str = os.getenv('BOT_MANUAL_ANSWER_PREFIX', '.mans')
    BOT_PREFERENCE_PREFIX: str = os.getenv('BOT_PREFERENCE_PREFIX', '.pref')
    MAX_QUESTION_LENGTH: int = int(os.getenv('MAX_QUESTION_LENGTH', 500))
    RESPONSE_TIMEOUT: int = int(os.getenv('RESPONSE_TIMEOUT', 30))

    # Chat analysis settings
    CHAT_HISTORY_LIMIT: int = int(os.getenv('CHAT_HISTORY_LIMIT', 10))
    MIN_OWNER_MESSAGES: int = int(os.getenv('MIN_OWNER_MESSAGES', 3))
    MAX_STYLE_SAMPLE_LENGTH: int = int(os.getenv('MAX_STYLE_SAMPLE_LENGTH', 2000))

    # Message settings
    INFO_MESSAGE_DELETE_DELAY: int = int(os.getenv('INFO_MESSAGE_DELETE_DELAY', 5))

    # Typing simulation settings
    TYPING_SPEED_WPM: int = int(os.getenv('TYPING_SPEED_WPM', 60))  # Words per minute
    TYPING_MIN_DELAY: float = float(os.getenv('TYPING_MIN_DELAY', 1.0))  # Minimum delay in seconds
    TYPING_MAX_DELAY: float = float(os.getenv('TYPING_MAX_DELAY', 8.0))  # Maximum delay in seconds
    TYPING_VARIATION: float = float(os.getenv('TYPING_VARIATION', 0.3))  # Speed variation (±30%)
    TYPING_PAUSE_CHANCE: float = float(os.getenv('TYPING_PAUSE_CHANCE', 0.2))  # Chance of thinking pause

    # Preference settings
    MAX_PREFERENCE_LENGTH: int = int(os.getenv('MAX_PREFERENCE_LENGTH', 200))  # Max length of preference text
    PREFERENCES_FILE: str = os.getenv('PREFERENCES_FILE', 'user_preferences.json')  # File to store preferences
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv('RATE_LIMIT_REQUESTS', 10))
    RATE_LIMIT_PERIOD: int = int(os.getenv('RATE_LIMIT_PERIOD', 60))
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'bot.log')
    
    # Session file
    SESSION_FILE: str = os.getenv('SESSION_FILE', 'telegram_session')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        required_fields = [
            'TELEGRAM_API_ID',
            'TELEGRAM_API_HASH', 
            'TELEGRAM_PHONE',
            'OPENAI_API_KEY'
        ]
        
        missing_fields = []
        for field in required_fields:
            value = getattr(cls, field)
            if not value or (isinstance(value, int) and value == 0):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            print("Please check your .env file and ensure all required fields are set.")
            return False
        
        return True
