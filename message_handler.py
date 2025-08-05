import asyncio
from typing import Optional, Dict, Any
from telethon.tl.types import Message, Chat, User, Channel
from asyncio_throttle import Throttler
from message_parser import MessageParser, ParsedCommand
from ai_client import AIClient, AIResponse
from chat_analyzer import ChatAnalyzer, ChatAnalysis
from auto_response_manager import auto_response_manager
from typing_simulator import typing_simulator
from preference_manager import preference_manager
from config import Config
from logger import setup_logger

logger = setup_logger(__name__)

class MessageHandler:
    """Handles message processing and replacement logic."""

    def __init__(self, owner_id: Optional[int] = None):
        """Initialize the message handler.

        Args:
            owner_id: Telegram user ID of the bot owner (for style analysis)
        """
        self.parser = MessageParser()
        self.ai_client = AIClient()
        self.owner_id = owner_id
        self.chat_analyzer = ChatAnalyzer(owner_id) if owner_id else None

        # Rate limiting to prevent abuse
        self.throttler = Throttler(
            rate_limit=Config.RATE_LIMIT_REQUESTS,
            period=Config.RATE_LIMIT_PERIOD
        )

        # Track processing status
        self.processing_messages = set()
    
    def set_owner_id(self, owner_id: int):
        """Set the owner ID after initialization.

        Args:
            owner_id: Telegram user ID of the bot owner
        """
        self.owner_id = owner_id
        self.chat_analyzer = ChatAnalyzer(owner_id)

    async def handle_message(self, event, question: str) -> bool:
        """Handle a detected command message.

        Args:
            event: Telegram event containing the message
            question: Extracted question from the message

        Returns:
            bool: True if successfully processed, False otherwise
        """
        message = event.message
        message_id = message.id

        # Security check: Only allow owner to use commands
        if self.owner_id and message.sender_id != self.owner_id:
            logger.warning(f"Non-owner user {message.sender_id} attempted to use bot command")
            return False

        # Prevent duplicate processing
        if message_id in self.processing_messages:
            logger.debug(f"Message {message_id} already being processed")
            return False

        self.processing_messages.add(message_id)
        
        try:
            # Apply rate limiting
            async with self.throttler:
                return await self._process_message(message, question)
                
        except Exception as e:
            logger.error(f"Error handling message {message_id}: {e}")
            return False
        finally:
            self.processing_messages.discard(message_id)
    
    async def _process_message(self, message: Message, question: str) -> bool:
        """Process a single message with AI response.
        
        Args:
            message: The original Telegram message
            question: The extracted question
            
        Returns:
            bool: True if successfully processed, False otherwise
        """
        try:
            logger.info(f"Processing message with question: {question[:50]}...")
            
            # Parse the message to validate
            parsed = self.parser.parse_message(message.message)
            if not parsed.is_valid:
                logger.warning(f"Invalid command: {parsed.error_message}")
                return False

            # Get chat context
            context = await self._get_message_context(message)

            # Generate AI response based on command type
            if parsed.command_type == "question":
                ai_response = await self.ai_client.generate_response(question, context)
            elif parsed.command_type == "answer":
                ai_response = await self._handle_answer_command(message, context)
            elif parsed.command_type == "auto_answer":
                ai_response = await self._handle_auto_answer_command(message, context)
            elif parsed.command_type == "manual_answer":
                ai_response = await self._handle_manual_answer_command(message, context)
            elif parsed.command_type == "preference":
                ai_response = await self._handle_preference_command(message, context, parsed.preferences)
            else:
                logger.error(f"Unknown command type: {parsed.command_type}")
                return False

            if not ai_response.success:
                logger.error(f"AI response failed: {ai_response.error_message}")
                await self._send_error_message(message, ai_response.error_message)
                return False

            # Check if AI decided to skip responding
            if ai_response.should_skip:
                logger.info("AI decided to skip responding - deleting command message silently")
                try:
                    await message.delete()
                    return True
                except Exception as e:
                    logger.warning(f"Failed to delete skip command message: {e}")
                    return False

            # Handle different response types
            if parsed.command_type in ["auto_answer", "manual_answer", "preference"]:
                # For info messages, send and auto-delete
                success = await self._send_and_delete_info_message(message, ai_response.response_text)
            else:
                # For regular responses, replace the original message
                success = await self._replace_message(message, ai_response.response_text)

            if success:
                logger.info(f"Successfully processed {parsed.command_type} command")
                if ai_response.tokens_used:
                    logger.debug(f"Tokens used: {ai_response.tokens_used}")

            return success
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False

    async def _handle_answer_command(self, message: Message, context: Dict[str, Any]) -> AIResponse:
        """Handle .ans command by analyzing chat history and generating style-based response.

        Args:
            message: The original message containing the .ans command
            context: Message context information

        Returns:
            AIResponse: The generated response or error information
        """
        try:
            if not self.chat_analyzer:
                return AIResponse(
                    success=False,
                    response_text="",
                    error_message="Chat analysis not available (owner ID not set)"
                )

            logger.info("Processing .ans command - analyzing chat history")

            # Get chat entity
            chat = await message.get_chat()
            if not chat:
                return AIResponse(
                    success=False,
                    response_text="",
                    error_message="Could not access chat information"
                )

            # Analyze chat history
            analysis = await self.chat_analyzer.analyze_chat(
                message.client,
                chat,
                exclude_message_id=message.id
            )

            if not analysis.is_valid_for_response:
                return AIResponse(
                    success=False,
                    response_text="",
                    error_message=analysis.error_message or "Chat analysis failed"
                )

            logger.info(f"Chat analysis successful: responding to {analysis.last_non_owner_message.sender_name}")

            # Get chat ID for preferences
            chat_id = message.peer_id.channel_id if hasattr(message.peer_id, 'channel_id') else message.peer_id.chat_id if hasattr(message.peer_id, 'chat_id') else message.peer_id.user_id

            # Get user preferences for this chat
            preferences_text = preference_manager.get_preferences_text(chat_id)

            # Generate response in owner's style
            ai_response = await self.ai_client.generate_style_response(
                analysis.context_summary,
                analysis.owner_style_sample,
                context,
                preferences_text if preferences_text else None
            )

            return ai_response

        except Exception as e:
            logger.error(f"Error handling answer command: {e}")
            return AIResponse(
                success=False,
                response_text="",
                error_message=f"Error analyzing chat: {str(e)}"
            )

    async def _handle_auto_answer_command(self, message: Message, context: Dict[str, Any]) -> AIResponse:
        """Handle .aans command to enable automatic answering.

        Args:
            message: The original message containing the .aans command
            context: Message context information

        Returns:
            AIResponse: Success/failure response
        """
        try:
            chat = await message.get_chat()
            if not chat:
                return AIResponse(
                    success=False,
                    response_text="",
                    error_message="Could not access chat information"
                )

            chat_id = message.peer_id.channel_id if hasattr(message.peer_id, 'channel_id') else message.peer_id.chat_id if hasattr(message.peer_id, 'chat_id') else message.peer_id.user_id

            success = auto_response_manager.enable_auto_response(chat_id)

            if success:
                chat_title = getattr(chat, 'title', 'this chat')
                response_text = f"🤖 Automatic answering enabled for {chat_title}! I'll respond to messages in your style."
                logger.info(f"Auto-response enabled for chat {chat_id}")
            else:
                response_text = "❌ Failed to enable automatic answering."

            return AIResponse(
                success=success,
                response_text=response_text,
                error_message=None if success else "Failed to enable auto-response"
            )

        except Exception as e:
            logger.error(f"Error handling auto-answer command: {e}")
            return AIResponse(
                success=False,
                response_text="",
                error_message=f"Error enabling auto-response: {str(e)}"
            )

    async def _handle_manual_answer_command(self, message: Message, context: Dict[str, Any]) -> AIResponse:
        """Handle .mans command to disable automatic answering.

        Args:
            message: The original message containing the .mans command
            context: Message context information

        Returns:
            AIResponse: Success/failure response
        """
        try:
            chat = await message.get_chat()
            if not chat:
                return AIResponse(
                    success=False,
                    response_text="",
                    error_message="Could not access chat information"
                )

            chat_id = message.peer_id.channel_id if hasattr(message.peer_id, 'channel_id') else message.peer_id.chat_id if hasattr(message.peer_id, 'chat_id') else message.peer_id.user_id

            success = auto_response_manager.disable_auto_response(chat_id)

            if success:
                chat_title = getattr(chat, 'title', 'this chat')
                response_text = f"🔇 Automatic answering disabled for {chat_title}. Use .ans for manual responses."
                logger.info(f"Auto-response disabled for chat {chat_id}")
            else:
                response_text = "⚠️ Automatic answering was not enabled for this chat."

            return AIResponse(
                success=True,  # Always consider this successful, even if it wasn't enabled
                response_text=response_text,
                error_message=None
            )

        except Exception as e:
            logger.error(f"Error handling manual-answer command: {e}")
            return AIResponse(
                success=False,
                response_text="",
                error_message=f"Error disabling auto-response: {str(e)}"
            )

    async def _handle_preference_command(self, message: Message, context: Dict[str, Any], preferences_text: Optional[str]) -> AIResponse:
        """Handle .pref command to set user preferences.

        Args:
            message: The original message containing the .pref command
            context: Message context information
            preferences_text: The preferences text to set

        Returns:
            AIResponse: Success/failure response
        """
        try:
            # Get chat ID
            chat_id = message.peer_id.channel_id if hasattr(message.peer_id, 'channel_id') else message.peer_id.chat_id if hasattr(message.peer_id, 'chat_id') else message.peer_id.user_id

            if not preferences_text or not preferences_text.strip():
                # Clear preferences
                success = preference_manager.set_preferences(chat_id, "")
                if success:
                    response_text = "🗑️ Preferences cleared for this chat."
                else:
                    response_text = "❌ Failed to clear preferences."
            else:
                # Set new preferences
                success = preference_manager.set_preferences(chat_id, preferences_text.strip())
                if success:
                    # Get the parsed preferences for confirmation
                    current_prefs = preference_manager.get_preferences(chat_id)
                    if current_prefs:
                        prefs_display = ", ".join(current_prefs)
                        response_text = f"✅ Preferences set: {prefs_display}"
                    else:
                        response_text = "✅ Preferences updated."
                else:
                    response_text = "❌ Failed to set preferences."

            logger.info(f"Preference command processed for chat {chat_id}: {preferences_text}")

            return AIResponse(
                success=True,
                response_text=response_text,
                error_message=None
            )

        except Exception as e:
            logger.error(f"Error handling preference command: {e}")
            return AIResponse(
                success=False,
                response_text="",
                error_message=f"Error setting preferences: {str(e)}"
            )
    
    async def _get_message_context(self, message: Message) -> Dict[str, Any]:
        """Extract context information from the message.
        
        Args:
            message: The Telegram message
            
        Returns:
            Dict[str, Any]: Context information
        """
        context = {}
        
        try:
            # Get chat information
            chat = await message.get_chat()
            if chat:
                if isinstance(chat, (Chat, Channel)):
                    context['chat_title'] = getattr(chat, 'title', 'Unknown')
                    context['chat_type'] = 'group' if isinstance(chat, Chat) else 'channel'
                elif isinstance(chat, User):
                    context['chat_title'] = f"{chat.first_name or ''} {chat.last_name or ''}".strip()
                    context['chat_type'] = 'private'
            
            # Get sender information
            sender = await message.get_sender()
            if sender and isinstance(sender, User):
                context['user_name'] = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                if sender.username:
                    context['user_username'] = sender.username
            
        except Exception as e:
            logger.warning(f"Error getting message context: {e}")
        
        return context
    
    async def _replace_message(self, original_message: Message, new_text: str) -> bool:
        """Replace the original message with new text with typing simulation.

        Args:
            original_message: The original message to replace
            new_text: The new text to send

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Store message details before deletion
            peer_id = original_message.peer_id
            reply_to = original_message.reply_to_msg_id

            # Delete the original message
            await original_message.delete()
            logger.debug("Original message deleted")

            # Get chat entity for typing simulation
            chat = await original_message.get_chat()

            # Simulate typing
            await typing_simulator.simulate_typing(original_message.client, chat, new_text)

            # Send the new message
            await original_message.client.send_message(
                peer_id,
                new_text,
                reply_to=reply_to
            )
            logger.debug("Replacement message sent with typing simulation")

            return True

        except Exception as e:
            logger.error(f"Failed to replace message: {e}")
            return False

    async def _send_and_delete_info_message(self, original_message: Message, info_text: str) -> bool:
        """Send an info message with typing simulation and auto-delete it after a delay.

        Args:
            original_message: The original command message
            info_text: The info text to send

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete the original command message first
            await original_message.delete()
            logger.debug("Original command message deleted")

            # Get chat entity for typing simulation
            chat = await original_message.get_chat()

            # Simulate quick typing for info messages
            await typing_simulator.simulate_quick_typing(original_message.client, chat, 1.5)

            # Send the info message
            sent_message = await original_message.client.send_message(
                original_message.peer_id,
                info_text
            )
            logger.debug("Info message sent with typing simulation")

            # Schedule auto-deletion
            async def delete_after_delay():
                try:
                    await asyncio.sleep(Config.INFO_MESSAGE_DELETE_DELAY)
                    await sent_message.delete()
                    logger.debug("Info message auto-deleted")
                except Exception as e:
                    logger.warning(f"Failed to auto-delete info message: {e}")

            # Start the deletion task in background
            asyncio.create_task(delete_after_delay())

            return True

        except Exception as e:
            logger.error(f"Failed to send and delete info message: {e}")
            return False
    
    async def _send_error_message(self, original_message: Message, error: str) -> None:
        """Send an error message when AI processing fails.
        
        Args:
            original_message: The original message
            error: Error description
        """
        try:
            error_text = f"❌ Error processing request: {error}"
            
            # Try to edit the original message first
            try:
                await original_message.edit(error_text)
                logger.debug("Error message sent via edit")
                return
            except:
                pass
            
            # If editing fails, send a new message
            await original_message.reply(error_text)
            logger.debug("Error message sent via reply")
            
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def handle_incoming_message(self, event) -> bool:
        """Handle incoming messages for potential auto-response.

        Args:
            event: Telegram event containing the message

        Returns:
            bool: True if message was processed (auto-responded), False otherwise
        """
        try:
            message = event.message

            # Skip if no owner ID set
            if not self.owner_id:
                return False

            # Skip owner's own messages
            if message.sender_id == self.owner_id:
                return False

            # Skip empty messages
            if not message.text or not message.text.strip():
                return False

            # Skip bot commands
            if self.parser.is_command_message(message.text):
                return False

            # Get chat ID
            chat_id = message.peer_id.channel_id if hasattr(message.peer_id, 'channel_id') else message.peer_id.chat_id if hasattr(message.peer_id, 'chat_id') else message.peer_id.user_id

            # Check if should auto-respond
            if not auto_response_manager.should_auto_respond(chat_id, message.sender_id, self.owner_id):
                return False

            logger.info(f"Auto-responding to message from {message.sender_id} in chat {chat_id}")

            # Get context
            context = await self._get_message_context(message)

            # Generate style-based response (this will automatically include preferences)
            ai_response = await self._handle_answer_command(message, context)

            if ai_response.success:
                # Check if AI decided to skip responding
                if ai_response.should_skip:
                    logger.info("AI decided to skip auto-responding to this message")
                    # Record the skip
                    auto_response_manager.record_skip(chat_id)
                    return True  # Consider this successful (no response needed)

                # Get chat entity for typing simulation
                chat = await message.get_chat()

                # Simulate typing for auto-response
                await typing_simulator.simulate_typing(message.client, chat, ai_response.response_text)

                # Send response (don't delete original message for auto-responses)
                await message.client.send_message(
                    message.peer_id,
                    ai_response.response_text,
                    reply_to=message.id
                )

                # Record the auto-response
                auto_response_manager.record_auto_response(chat_id)
                logger.info("Auto-response sent successfully with typing simulation")
                return True
            else:
                logger.warning(f"Auto-response failed: {ai_response.error_message}")
                return False

        except Exception as e:
            logger.error(f"Error handling incoming message for auto-response: {e}")
            return False

    async def test_ai_connection(self) -> bool:
        """Test the AI client connection.

        Returns:
            bool: True if AI is working, False otherwise
        """
        return await self.ai_client.test_connection()
