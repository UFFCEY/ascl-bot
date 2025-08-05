import asyncio
import re
from typing import Optional, Callable, Any
from telethon import TelegramClient, events
from telethon.tl.types import Message
from config import Config
from logger import setup_logger

logger = setup_logger(__name__)

class TelegramBotClient:
    """Telegram client for monitoring and replacing messages."""
    
    def __init__(self, message_handler: Optional[Callable] = None):
        """Initialize the Telegram client.
        
        Args:
            message_handler: Callback function to handle detected commands
        """
        self.client = TelegramClient(
            Config.SESSION_FILE,
            Config.TELEGRAM_API_ID,
            Config.TELEGRAM_API_HASH
        )
        self.message_handler = message_handler
        # Patterns for all command types
        self.command_pattern = re.compile(
            rf'^{re.escape(Config.BOT_COMMAND_PREFIX)}\s+(.+)$',
            re.IGNORECASE | re.DOTALL
        )
        self.answer_pattern = re.compile(
            rf'^{re.escape(Config.BOT_ANSWER_PREFIX)}(?:\s+.*)?$',
            re.IGNORECASE | re.DOTALL
        )
        self.auto_answer_pattern = re.compile(
            rf'^{re.escape(Config.BOT_AUTO_ANSWER_PREFIX)}(?:\s+.*)?$',
            re.IGNORECASE | re.DOTALL
        )
        self.manual_answer_pattern = re.compile(
            rf'^{re.escape(Config.BOT_MANUAL_ANSWER_PREFIX)}(?:\s+.*)?$',
            re.IGNORECASE | re.DOTALL
        )
        self.preference_pattern = re.compile(
            rf'^{re.escape(Config.BOT_PREFERENCE_PREFIX)}(?:\s+.*)?$',
            re.IGNORECASE | re.DOTALL
        )
        
    async def start(self) -> bool:
        """Start the Telegram client and authenticate."""
        try:
            logger.info("Starting Telegram client...")
            await self.client.start(phone=Config.TELEGRAM_PHONE)
            
            # Verify authentication
            me = await self.client.get_me()
            logger.info(f"Successfully authenticated as {me.first_name} (@{me.username})")
            
            # Register event handlers
            self._register_handlers()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
            return False
    
    async def stop(self):
        """Stop the Telegram client."""
        try:
            logger.info("Stopping Telegram client...")
            await self.client.disconnect()
            logger.info("Telegram client stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram client: {e}")
    
    def _register_handlers(self):
        """Register event handlers for message monitoring."""
        
        @self.client.on(events.NewMessage(outgoing=True))
        async def handle_outgoing_message(event):
            """Handle outgoing messages to detect commands."""
            try:
                message_text = event.message.message
                if not message_text:
                    return
                
                # Check if message matches command patterns
                command_match = self.command_pattern.match(message_text.strip())
                answer_match = self.answer_pattern.match(message_text.strip())
                auto_answer_match = self.auto_answer_pattern.match(message_text.strip())
                manual_answer_match = self.manual_answer_pattern.match(message_text.strip())
                preference_match = self.preference_pattern.match(message_text.strip())

                if command_match:
                    question = command_match.group(1).strip()

                    if len(question) > Config.MAX_QUESTION_LENGTH:
                        logger.warning(f"Question too long ({len(question)} chars), skipping")
                        return

                    logger.info(f"Detected .ascl command with question: {question[:50]}...")

                    # Call the message handler if provided
                    if self.message_handler:
                        if callable(self.message_handler):
                            await self.message_handler(event, question)
                        else:
                            await self.message_handler.handle_message(event, question)

                elif answer_match:
                    logger.info("Detected .ans command")

                    # Call the message handler with empty question for .ans command
                    if self.message_handler:
                        if callable(self.message_handler):
                            await self.message_handler(event, "")
                        else:
                            await self.message_handler.handle_message(event, "")

                elif auto_answer_match:
                    logger.info("Detected .aans command")

                    # Call the message handler for auto-answer command
                    if self.message_handler:
                        if callable(self.message_handler):
                            await self.message_handler(event, "")
                        else:
                            await self.message_handler.handle_message(event, "")

                elif manual_answer_match:
                    logger.info("Detected .mans command")

                    # Call the message handler for manual-answer command
                    if self.message_handler:
                        if callable(self.message_handler):
                            await self.message_handler(event, "")
                        else:
                            await self.message_handler.handle_message(event, "")

                elif preference_match:
                    logger.info("Detected .pref command")

                    # Call the message handler for preference command
                    if self.message_handler:
                        if callable(self.message_handler):
                            await self.message_handler(event, "")
                        else:
                            await self.message_handler.handle_message(event, "")
                        
            except Exception as e:
                logger.error(f"Error handling outgoing message: {e}")

        @self.client.on(events.NewMessage(incoming=True))
        async def handle_incoming_message(event):
            """Handle incoming messages for potential auto-response and command blocking."""
            try:
                message_text = event.message.message
                if not message_text:
                    return

                # Check if non-owner is trying to use bot commands
                if self._is_bot_command(message_text):
                    logger.warning(f"Non-owner user {event.message.sender_id} attempted to use bot command: {message_text[:20]}...")
                    # Silently ignore - don't respond to prevent revealing bot presence
                    return

                # Only process if we have a message handler
                if not self.message_handler:
                    return

                # Let the message handler decide if this should trigger an auto-response
                if hasattr(self.message_handler, 'handle_incoming_message'):
                    await self.message_handler.handle_incoming_message(event)

            except Exception as e:
                logger.error(f"Error handling incoming message: {e}")

    def _is_bot_command(self, message_text: str) -> bool:
        """Check if a message is a bot command.

        Args:
            message_text: The message text to check

        Returns:
            bool: True if it's a bot command
        """
        if not message_text:
            return False

        text_lower = message_text.strip().lower()
        return (text_lower.startswith(Config.BOT_COMMAND_PREFIX.lower()) or
                text_lower.startswith(Config.BOT_ANSWER_PREFIX.lower()) or
                text_lower.startswith(Config.BOT_AUTO_ANSWER_PREFIX.lower()) or
                text_lower.startswith(Config.BOT_MANUAL_ANSWER_PREFIX.lower()) or
                text_lower.startswith(Config.BOT_PREFERENCE_PREFIX.lower()))
    
    async def replace_message(self, original_message: Message, new_text: str) -> bool:
        """Replace an original message with new text.
        
        Args:
            original_message: The original message to replace
            new_text: The new text to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete the original message
            await original_message.delete()
            logger.debug("Original message deleted")
            
            # Send the new message
            await self.client.send_message(
                original_message.peer_id,
                new_text,
                reply_to=original_message.reply_to_msg_id
            )
            logger.debug("Replacement message sent")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to replace message: {e}")
            return False
    
    async def run_until_disconnected(self):
        """Run the client until disconnected."""
        try:
            logger.info("Bot is running. Press Ctrl+C to stop.")
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            await self.stop()
