import re
from typing import Optional, Tuple
from dataclasses import dataclass
from config import Config
from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ParsedCommand:
    """Represents a parsed command from a message."""
    original_text: str
    command: str
    command_type: str  # 'question' for .ascl, 'answer' for .ans, 'auto_answer' for .aans, 'manual_answer' for .mans, 'preference' for .pref
    question: str
    is_valid: bool
    preferences: Optional[str] = None  # For .pref commands
    error_message: Optional[str] = None

class MessageParser:
    """Parser for detecting and extracting commands from messages."""
    
    def __init__(self):
        """Initialize the message parser."""
        self.command_prefix = Config.BOT_COMMAND_PREFIX
        self.answer_prefix = Config.BOT_ANSWER_PREFIX
        self.auto_answer_prefix = Config.BOT_AUTO_ANSWER_PREFIX
        self.manual_answer_prefix = Config.BOT_MANUAL_ANSWER_PREFIX
        self.preference_prefix = Config.BOT_PREFERENCE_PREFIX
        self.max_question_length = Config.MAX_QUESTION_LENGTH

        # Create regex patterns for command detection
        escaped_command_prefix = re.escape(self.command_prefix)
        escaped_answer_prefix = re.escape(self.answer_prefix)
        escaped_auto_answer_prefix = re.escape(self.auto_answer_prefix)
        escaped_manual_answer_prefix = re.escape(self.manual_answer_prefix)
        escaped_preference_prefix = re.escape(self.preference_prefix)

        self.command_pattern = re.compile(
            rf'^{escaped_command_prefix}\s+(.+)$',
            re.IGNORECASE | re.DOTALL
        )

        self.answer_pattern = re.compile(
            rf'^{escaped_answer_prefix}(?:\s+(.*))?$',
            re.IGNORECASE | re.DOTALL
        )

        self.auto_answer_pattern = re.compile(
            rf'^{escaped_auto_answer_prefix}(?:\s+(.*))?$',
            re.IGNORECASE | re.DOTALL
        )

        self.manual_answer_pattern = re.compile(
            rf'^{escaped_manual_answer_prefix}(?:\s+(.*))?$',
            re.IGNORECASE | re.DOTALL
        )

        self.preference_pattern = re.compile(
            rf'^{escaped_preference_prefix}(?:\s+(.*))?$',
            re.IGNORECASE | re.DOTALL
        )

        # Pattern for cleaning up the question text
        self.whitespace_pattern = re.compile(r'\s+')
        
    def parse_message(self, message_text: str) -> ParsedCommand:
        """Parse a message to extract command and question.
        
        Args:
            message_text: The message text to parse
            
        Returns:
            ParsedCommand: Parsed command information
        """
        if not message_text:
            return ParsedCommand(
                original_text="",
                command="",
                command_type="",
                question="",
                preferences=None,
                is_valid=False,
                error_message="Empty message"
            )
        
        # Clean the message text
        cleaned_text = message_text.strip()

        # Check if message matches command patterns
        command_match = self.command_pattern.match(cleaned_text)
        answer_match = self.answer_pattern.match(cleaned_text)
        auto_answer_match = self.auto_answer_pattern.match(cleaned_text)
        manual_answer_match = self.manual_answer_pattern.match(cleaned_text)
        preference_match = self.preference_pattern.match(cleaned_text)

        preferences = None

        if command_match:
            # .ascl <question> command
            raw_question = command_match.group(1)
            question = self._clean_question(raw_question)
            command_type = "question"
            command = self.command_prefix
        elif answer_match:
            # .ans command (no question needed)
            question = ""
            command_type = "answer"
            command = self.answer_prefix
        elif auto_answer_match:
            # .aans command (enable auto-answering)
            question = ""
            command_type = "auto_answer"
            command = self.auto_answer_prefix
        elif manual_answer_match:
            # .mans command (disable auto-answering)
            question = ""
            command_type = "manual_answer"
            command = self.manual_answer_prefix
        elif preference_match:
            # .pref command (set preferences)
            question = ""
            command_type = "preference"
            command = self.preference_prefix
            preferences = preference_match.group(1) if preference_match.group(1) else ""
        else:
            return ParsedCommand(
                original_text=message_text,
                command="",
                command_type="",
                question="",
                preferences=None,
                is_valid=False,
                error_message="Message does not match any command pattern"
            )
        
        # Validate question (only for question commands)
        if command_type == "question":
            validation_error = self._validate_question(question)
            if validation_error:
                return ParsedCommand(
                    original_text=message_text,
                    command=command,
                    command_type=command_type,
                    question=question,
                    preferences=preferences,
                    is_valid=False,
                    error_message=validation_error
                )

        return ParsedCommand(
            original_text=message_text,
            command=command,
            command_type=command_type,
            question=question,
            preferences=preferences,
            is_valid=True
        )
    
    def _clean_question(self, raw_question: str) -> str:
        """Clean and normalize the question text.
        
        Args:
            raw_question: Raw question text from regex match
            
        Returns:
            str: Cleaned question text
        """
        # Remove excessive whitespace and normalize
        cleaned = self.whitespace_pattern.sub(' ', raw_question.strip())
        
        # Remove common artifacts
        cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
        
        return cleaned
    
    def _validate_question(self, question: str) -> Optional[str]:
        """Validate the extracted question.
        
        Args:
            question: The question to validate
            
        Returns:
            Optional[str]: Error message if invalid, None if valid
        """
        if not question:
            return "Question is empty"
        
        if len(question) > self.max_question_length:
            return f"Question too long ({len(question)} chars, max {self.max_question_length})"
        
        # Check for minimum meaningful length
        if len(question.strip()) < 3:
            return "Question too short"
        
        # Check for suspicious patterns that might indicate spam or abuse
        suspicious_patterns = [
            r'^(.)\1{10,}',  # Repeated characters
            r'[^\w\s\?\!\.\,\-\(\)]{5,}',  # Too many special characters
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, question):
                return "Question contains suspicious patterns"
        
        return None
    
    def is_command_message(self, message_text: str) -> bool:
        """Quick check if a message is a command.

        Args:
            message_text: The message text to check

        Returns:
            bool: True if message starts with any command prefix
        """
        if not message_text:
            return False

        text_lower = message_text.strip().lower()
        return (text_lower.startswith(self.command_prefix.lower()) or
                text_lower.startswith(self.answer_prefix.lower()) or
                text_lower.startswith(self.auto_answer_prefix.lower()) or
                text_lower.startswith(self.manual_answer_prefix.lower()) or
                text_lower.startswith(self.preference_prefix.lower()))
    
    def extract_question_preview(self, question: str, max_length: int = 50) -> str:
        """Extract a preview of the question for logging.
        
        Args:
            question: The full question text
            max_length: Maximum length of preview
            
        Returns:
            str: Truncated question with ellipsis if needed
        """
        if len(question) <= max_length:
            return question
        
        return question[:max_length-3] + "..."
