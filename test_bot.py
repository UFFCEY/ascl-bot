#!/usr/bin/env python3
"""
Test suite for Telegram AI Bot Client
"""

import unittest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from message_parser import MessageParser, ParsedCommand
from security import SecurityManager
from config import Config

class TestMessageParser(unittest.TestCase):
    """Test cases for message parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = MessageParser()
    
    def test_valid_command(self):
        """Test parsing valid commands."""
        test_cases = [
            (".ascl What is the capital of France?", "question"),
            (".ascl How does photosynthesis work?", "question"),
            (".ascl   What is 2+2?   ", "question"),  # Extra whitespace
            (".ASCL Case insensitive test", "question"),  # Case insensitive
            (".ans", "answer"),
            (".ANS", "answer"),  # Case insensitive
            (".ans ", "answer"),  # With trailing space
        ]

        for message, expected_type in test_cases:
            with self.subTest(message=message):
                result = self.parser.parse_message(message)
                self.assertTrue(result.is_valid)
                self.assertEqual(result.command_type, expected_type)
                if expected_type == "question":
                    self.assertGreater(len(result.question), 0)
                else:
                    self.assertEqual(result.question, "")
    
    def test_invalid_command(self):
        """Test parsing invalid commands."""
        test_cases = [
            "Just a regular message",
            ".ascl",  # No question
            ".ascl   ",  # Only whitespace
            "ascl Missing dot",
            ".other Different command",
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                result = self.parser.parse_message(message)
                self.assertFalse(result.is_valid)
    
    def test_question_length_validation(self):
        """Test question length validation."""
        # Too long question
        long_question = ".ascl " + "a" * (Config.MAX_QUESTION_LENGTH + 1)
        result = self.parser.parse_message(long_question)
        self.assertFalse(result.is_valid)
        self.assertIn("too long", result.error_message.lower())
        
        # Valid length question
        valid_question = ".ascl " + "a" * (Config.MAX_QUESTION_LENGTH - 10)
        result = self.parser.parse_message(valid_question)
        self.assertTrue(result.is_valid)
    
    def test_question_cleaning(self):
        """Test question text cleaning."""
        message = ".ascl   What    is\n\nthe   answer?   "
        result = self.parser.parse_message(message)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.question, "What is the answer?")
    
    def test_is_command_message(self):
        """Test quick command detection."""
        self.assertTrue(self.parser.is_command_message(".ascl test"))
        self.assertTrue(self.parser.is_command_message(".ASCL test"))
        self.assertTrue(self.parser.is_command_message("  .ascl test  "))
        self.assertTrue(self.parser.is_command_message(".ans"))
        self.assertTrue(self.parser.is_command_message(".ANS"))
        self.assertTrue(self.parser.is_command_message("  .ans  "))
        self.assertFalse(self.parser.is_command_message("not a command"))
        self.assertFalse(self.parser.is_command_message(""))

class TestSecurityManager(unittest.TestCase):
    """Test cases for security manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.security = SecurityManager()
        self.test_user_id = "test_user_123"
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # First requests should be allowed
        for i in range(self.security.max_requests_per_minute):
            self.assertTrue(self.security.check_rate_limit(self.test_user_id))
        
        # Next request should be rate limited
        self.assertFalse(self.security.check_rate_limit(self.test_user_id))
    
    def test_question_validation(self):
        """Test question content validation."""
        # Valid questions
        valid_questions = [
            "What is the weather today?",
            "How do I cook pasta?",
            "Explain quantum physics",
        ]
        
        for question in valid_questions:
            with self.subTest(question=question):
                result = self.security.validate_question(question, self.test_user_id)
                self.assertIsNone(result)
        
        # Invalid questions
        invalid_questions = [
            "a" * (Config.MAX_QUESTION_LENGTH + 1),  # Too long
            "aa",  # Too short
            "How to hack passwords",  # Blocked content
        ]
        
        for question in invalid_questions:
            with self.subTest(question=question):
                result = self.security.validate_question(question, self.test_user_id)
                self.assertIsNotNone(result)
    
    def test_user_id_generation(self):
        """Test secure user ID generation."""
        user_id1 = self.security.get_user_id(12345, 67890)
        user_id2 = self.security.get_user_id(12345, 67890)
        user_id3 = self.security.get_user_id(12345, 67891)
        
        # Same inputs should produce same ID
        self.assertEqual(user_id1, user_id2)
        
        # Different inputs should produce different IDs
        self.assertNotEqual(user_id1, user_id3)
        
        # IDs should be strings of reasonable length
        self.assertIsInstance(user_id1, str)
        self.assertGreater(len(user_id1), 10)

class TestConfig(unittest.TestCase):
    """Test cases for configuration."""
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Save original values
        original_values = {
            'TELEGRAM_API_ID': Config.TELEGRAM_API_ID,
            'TELEGRAM_API_HASH': Config.TELEGRAM_API_HASH,
            'TELEGRAM_PHONE': Config.TELEGRAM_PHONE,
            'OPENAI_API_KEY': Config.OPENAI_API_KEY,
        }
        
        try:
            # Test with missing values
            Config.TELEGRAM_API_ID = 0
            self.assertFalse(Config.validate())
            
            Config.TELEGRAM_API_ID = 12345
            Config.TELEGRAM_API_HASH = ""
            self.assertFalse(Config.validate())
            
            # Test with all values present
            Config.TELEGRAM_API_ID = 12345
            Config.TELEGRAM_API_HASH = "test_hash"
            Config.TELEGRAM_PHONE = "+1234567890"
            Config.OPENAI_API_KEY = "test_key"
            self.assertTrue(Config.validate())
            
        finally:
            # Restore original values
            for key, value in original_values.items():
                setattr(Config, key, value)

class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests."""
    
    async def test_message_flow(self):
        """Test complete message processing flow."""
        # This would require mocking Telegram and OpenAI APIs
        # For now, just test that components can be imported and initialized
        from main import TelegramAIBot
        
        bot = TelegramAIBot()
        self.assertIsNotNone(bot.message_handler)
        self.assertIsNone(bot.telegram_client)  # Not started yet
        self.assertFalse(bot.running)

def run_tests():
    """Run all tests."""
    print("🧪 Running Telegram AI Bot tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMessageParser))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} error(s) occurred")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
