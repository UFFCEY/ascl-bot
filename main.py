#!/usr/bin/env python3
"""
Telegram AI Bot Client

A Telegram bot client that monitors your messages and replaces .ascl <question> 
commands with AI-generated responses.

Usage:
    python main.py

Requirements:
    - Telegram API credentials (API ID, API Hash, Phone)
    - OpenAI API key
    - Python 3.8+
"""

import asyncio
import signal
import sys
from typing import Optional
from config import Config
from logger import setup_logger
from telegram_client import TelegramBotClient
from message_handler import MessageHandler
from security import security_manager
from error_handler import error_handler

logger = setup_logger(__name__)

class TelegramAIBot:
    """Main bot class that coordinates all components."""
    
    def __init__(self):
        """Initialize the bot."""
        self.message_handler = MessageHandler()
        self.telegram_client: Optional[TelegramBotClient] = None
        self.running = False
        
    async def start(self) -> bool:
        """Start the bot and all its components.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            logger.info("Starting Telegram AI Bot...")
            
            # Validate configuration
            if not Config.validate():
                logger.error("Configuration validation failed")
                return False
            
            # Test AI connection
            logger.info("Testing AI connection...")
            if not await self.message_handler.test_ai_connection():
                logger.error("AI connection test failed")
                return False
            logger.info("AI connection test passed")
            
            # Initialize Telegram client
            self.telegram_client = TelegramBotClient(
                message_handler=self._handle_command_message
            )

            # Set the message handler instance for incoming message processing
            self.telegram_client.message_handler = self.message_handler
            
            # Start Telegram client
            if not await self.telegram_client.start():
                logger.error("Failed to start Telegram client")
                return False

            # Get owner ID and set it in message handler
            me = await self.telegram_client.client.get_me()
            owner_id = me.id
            self.message_handler.set_owner_id(owner_id)
            logger.info(f"Owner ID set: {owner_id}")

            self.running = True
            logger.info("Bot started successfully!")
            logger.info(f"Monitoring for commands: {Config.BOT_COMMAND_PREFIX} <question>, {Config.BOT_ANSWER_PREFIX}, {Config.BOT_AUTO_ANSWER_PREFIX}, {Config.BOT_MANUAL_ANSWER_PREFIX}, {Config.BOT_PREFERENCE_PREFIX} <preferences>")

            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            return False
    
    async def stop(self):
        """Stop the bot and cleanup resources."""
        try:
            logger.info("Stopping bot...")
            self.running = False
            
            if self.telegram_client:
                await self.telegram_client.stop()
            
            # Cleanup security data
            security_manager.cleanup_old_data()
            
            logger.info("Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    async def _handle_command_message(self, event, question: str):
        """Handle detected command messages.
        
        Args:
            event: Telegram event
            question: Extracted question
        """
        try:
            # Get user identifier for security checks
            user_id = security_manager.get_user_id(
                event.message.sender_id,
                event.message.peer_id.user_id if hasattr(event.message.peer_id, 'user_id') else 0
            )
            
            # Check global rate limits
            if not security_manager.check_global_rate_limit():
                logger.warning("Global rate limit exceeded, ignoring request")
                return
            
            # Check user rate limits
            if not security_manager.check_rate_limit(user_id):
                logger.warning(f"User {user_id} rate limited")
                return
            
            # Validate question content (only for question commands)
            if question:  # Only validate if there's a question (.ascl commands)
                validation_error = security_manager.validate_question(question, user_id)
                if validation_error:
                    logger.warning(f"Question validation failed for user {user_id}: {validation_error}")
                    return
            
            # Process the message
            success = await self.message_handler.handle_message(event, question)
            
            if not success:
                security_manager.metrics.failed_requests += 1
                logger.warning(f"Failed to process message for user {user_id}")
            
        except Exception as e:
            error_handler.log_error_with_context(e, {
                'function': '_handle_command_message',
                'user_id': user_id if 'user_id' in locals() else 'unknown',
                'question_preview': question[:50] if question else 'none'
            })
    
    async def run(self):
        """Run the bot until stopped."""
        try:
            if not await self.start():
                return False
            
            # Set up signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, initiating shutdown...")
                self.running = False
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Run the Telegram client
            if self.telegram_client:
                await self.telegram_client.run_until_disconnected()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            await self.stop()
    
    def get_status(self) -> dict:
        """Get bot status information.
        
        Returns:
            dict: Status information
        """
        return {
            'running': self.running,
            'telegram_connected': self.telegram_client is not None,
            'security_stats': security_manager.get_security_stats(),
            'error_stats': error_handler.get_error_stats()
        }

async def main():
    """Main entry point."""
    try:
        logger.info("Telegram AI Bot starting...")
        
        bot = TelegramAIBot()
        success = await bot.run()
        
        if success:
            logger.info("Bot finished successfully")
            sys.exit(0)
        else:
            logger.error("Bot failed to start")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
