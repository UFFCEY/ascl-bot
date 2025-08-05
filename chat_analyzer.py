import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from telethon.tl.types import Message, User
from config import Config
from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ChatMessage:
    """Represents a message in the chat history."""
    id: int
    text: str
    sender_id: int
    sender_name: str
    is_owner: bool
    timestamp: float

@dataclass
class ChatAnalysis:
    """Results of chat history analysis."""
    recent_messages: List[ChatMessage]
    owner_messages: List[ChatMessage]
    last_non_owner_message: Optional[ChatMessage]
    context_summary: str
    owner_style_sample: str
    is_valid_for_response: bool
    chat_type: str = "unknown"  # "private", "group", "channel"
    is_message_directed_at_owner: bool = False  # For group chats
    error_message: Optional[str] = None

class ChatAnalyzer:
    """Analyzes chat history to understand context and owner's writing style."""
    
    def __init__(self, owner_id: int):
        """Initialize the chat analyzer.
        
        Args:
            owner_id: Telegram user ID of the bot owner
        """
        self.owner_id = owner_id
        self.history_limit = Config.CHAT_HISTORY_LIMIT
        self.min_owner_messages = Config.MIN_OWNER_MESSAGES
        self.max_style_sample = Config.MAX_STYLE_SAMPLE_LENGTH
    
    async def analyze_chat(self, client, chat_entity, exclude_message_id: Optional[int] = None) -> ChatAnalysis:
        """Analyze chat history to extract context and owner's style.
        
        Args:
            client: Telegram client instance
            chat_entity: Chat entity to analyze
            exclude_message_id: Message ID to exclude (usually the command message)
            
        Returns:
            ChatAnalysis: Analysis results
        """
        try:
            logger.info(f"Analyzing chat history (limit: {self.history_limit})")
            
            # Fetch recent messages
            messages = await self._fetch_recent_messages(client, chat_entity, exclude_message_id)
            
            if not messages:
                return ChatAnalysis(
                    recent_messages=[],
                    owner_messages=[],
                    last_non_owner_message=None,
                    context_summary="",
                    owner_style_sample="",
                    is_valid_for_response=False,
                    error_message="No messages found in chat history"
                )
            
            # Convert to ChatMessage objects
            chat_messages = await self._convert_to_chat_messages(client, messages)
            
            # Separate owner and non-owner messages
            owner_messages = [msg for msg in chat_messages if msg.is_owner]
            non_owner_messages = [msg for msg in chat_messages if not msg.is_owner]

            # Debug logging
            logger.info(f"Owner ID: {self.owner_id}")
            logger.info(f"Total messages: {len(chat_messages)}")
            logger.info(f"Owner messages: {len(owner_messages)}")
            logger.info(f"Non-owner messages: {len(non_owner_messages)}")

            for msg in chat_messages[:3]:  # Log first 3 messages for debugging
                logger.debug(f"Message from {msg.sender_id} ({msg.sender_name}): is_owner={msg.is_owner}, text='{msg.text[:50]}...'")
            
            # Find the last non-owner message
            last_non_owner = non_owner_messages[0] if non_owner_messages else None
            
            # Check if we have enough data for a good response
            if not last_non_owner:
                return ChatAnalysis(
                    recent_messages=chat_messages,
                    owner_messages=owner_messages,
                    last_non_owner_message=None,
                    context_summary="",
                    owner_style_sample="",
                    is_valid_for_response=False,
                    error_message="No recent messages from other users to respond to"
                )
            
            if len(owner_messages) < self.min_owner_messages:
                return ChatAnalysis(
                    recent_messages=chat_messages,
                    owner_messages=owner_messages,
                    last_non_owner_message=last_non_owner,
                    context_summary="",
                    owner_style_sample="",
                    is_valid_for_response=False,
                    error_message=f"Not enough owner messages for style analysis (need {self.min_owner_messages}, found {len(owner_messages)})"
                )
            
            # Determine chat type and if message is directed at owner
            chat_type, is_directed = await self._analyze_chat_context(client, chat_entity, last_non_owner)

            # Generate context summary
            context_summary = self._generate_context_summary(chat_messages, last_non_owner, chat_type, is_directed)

            # Extract owner's writing style
            owner_style_sample = self._extract_owner_style(owner_messages)

            logger.info(f"Chat analysis complete: {len(chat_messages)} messages, {len(owner_messages)} owner messages, type: {chat_type}")

            return ChatAnalysis(
                recent_messages=chat_messages,
                owner_messages=owner_messages,
                last_non_owner_message=last_non_owner,
                context_summary=context_summary,
                owner_style_sample=owner_style_sample,
                is_valid_for_response=True,
                chat_type=chat_type,
                is_message_directed_at_owner=is_directed
            )
            
        except Exception as e:
            logger.error(f"Error analyzing chat: {e}")
            return ChatAnalysis(
                recent_messages=[],
                owner_messages=[],
                last_non_owner_message=None,
                context_summary="",
                owner_style_sample="",
                is_valid_for_response=False,
                error_message=f"Error analyzing chat: {str(e)}"
            )
    
    async def _fetch_recent_messages(self, client, chat_entity, exclude_message_id: Optional[int]) -> List[Message]:
        """Fetch recent messages from the chat.
        
        Args:
            client: Telegram client
            chat_entity: Chat to fetch from
            exclude_message_id: Message ID to exclude
            
        Returns:
            List[Message]: Recent messages
        """
        try:
            # Fetch more messages than needed to account for excluded ones
            fetch_limit = self.history_limit + 5
            
            messages = []
            async for message in client.iter_messages(chat_entity, limit=fetch_limit):
                # Skip the excluded message (usually the command)
                if exclude_message_id and message.id == exclude_message_id:
                    continue
                
                # Skip empty messages
                if not message.text or not message.text.strip():
                    continue
                
                # Skip bot commands
                if self._is_bot_command(message.text):
                    continue
                
                messages.append(message)
                
                # Stop when we have enough
                if len(messages) >= self.history_limit:
                    break
            
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []
    
    async def _convert_to_chat_messages(self, client, messages: List[Message]) -> List[ChatMessage]:
        """Convert Telegram messages to ChatMessage objects.
        
        Args:
            client: Telegram client
            messages: List of Telegram messages
            
        Returns:
            List[ChatMessage]: Converted messages
        """
        chat_messages = []
        
        for message in messages:
            try:
                # Get sender information
                sender = await message.get_sender()
                sender_name = "Unknown"
                
                if isinstance(sender, User):
                    sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                    if not sender_name:
                        sender_name = sender.username or f"User{sender.id}"
                
                chat_message = ChatMessage(
                    id=message.id,
                    text=message.text.strip(),
                    sender_id=message.sender_id,
                    sender_name=sender_name,
                    is_owner=(message.sender_id == self.owner_id),
                    timestamp=message.date.timestamp()
                )
                
                chat_messages.append(chat_message)
                
            except Exception as e:
                logger.warning(f"Error processing message {message.id}: {e}")
                continue
        
        return chat_messages
    
    def _is_bot_command(self, text: str) -> bool:
        """Check if a message is a bot command.
        
        Args:
            text: Message text
            
        Returns:
            bool: True if it's a bot command
        """
        if not text:
            return False
        
        text_lower = text.strip().lower()
        return (text_lower.startswith(Config.BOT_COMMAND_PREFIX.lower()) or 
                text_lower.startswith(Config.BOT_ANSWER_PREFIX.lower()))
    
    async def _analyze_chat_context(self, client, chat_entity, last_non_owner: ChatMessage) -> Tuple[str, bool]:
        """Analyze chat context to determine type and if message is directed at owner.

        Args:
            client: Telegram client
            chat_entity: Chat entity
            last_non_owner: Last message from non-owner

        Returns:
            Tuple[str, bool]: (chat_type, is_directed_at_owner)
        """
        try:
            from telethon.tl.types import Chat, Channel, User

            # Determine chat type
            if isinstance(chat_entity, User):
                chat_type = "private"
                is_directed = True  # In private chats, all messages are directed at owner
            elif isinstance(chat_entity, Chat):
                chat_type = "group"
                is_directed = self._is_message_directed_at_owner(last_non_owner)
            elif isinstance(chat_entity, Channel):
                if getattr(chat_entity, 'megagroup', False):
                    chat_type = "group"
                    is_directed = self._is_message_directed_at_owner(last_non_owner)
                else:
                    chat_type = "channel"
                    is_directed = False  # Usually don't respond in channels
            else:
                chat_type = "unknown"
                is_directed = False

            return chat_type, is_directed

        except Exception as e:
            logger.warning(f"Error analyzing chat context: {e}")
            return "unknown", False

    def _is_message_directed_at_owner(self, message: ChatMessage) -> bool:
        """Check if a message is directed at the owner.

        Args:
            message: Message to analyze

        Returns:
            bool: True if message seems directed at owner
        """
        try:
            text = message.text.lower()

            # Check for direct mentions or replies (this is simplified)
            # In a real implementation, you'd check for @username mentions
            directed_indicators = [
                "liminal", "лиминал",  # Owner's name variations
                "@", "ответь", "скажи", "что думаешь",  # Direct address indicators
                "?", "как дела", "привет", "hello"  # Question/greeting patterns
            ]

            # Simple heuristic: if message contains question marks or direct indicators
            for indicator in directed_indicators:
                if indicator in text:
                    return True

            # If message is very short and conversational, likely directed
            if len(text.split()) <= 3 and any(word in text for word in ["да", "нет", "ок", "хорошо", "плохо", "yes", "no", "ok"]):
                return True

            return False

        except Exception as e:
            logger.warning(f"Error checking if message is directed: {e}")
            return False

    def _generate_context_summary(self, messages: List[ChatMessage], last_non_owner: ChatMessage, chat_type: str = "unknown", is_directed: bool = False) -> str:
        """Generate a summary of the conversation context.

        Args:
            messages: Recent chat messages
            last_non_owner: Last message from non-owner
            chat_type: Type of chat (private, group, channel)
            is_directed: Whether the message is directed at the owner

        Returns:
            str: Context summary
        """
        try:
            # Get the last few messages for context
            context_messages = messages[:5]  # Last 5 messages

            # Find the owner's name from their messages
            owner_name = "You"
            for msg in messages:
                if msg.is_owner and msg.sender_name and msg.sender_name.strip():
                    owner_name = msg.sender_name
                    break

            context_parts = []
            context_parts.append(f"Recent conversation context:")
            context_parts.append(f"You are: {owner_name}")
            context_parts.append(f"Chat type: {chat_type}")

            if chat_type == "group":
                context_parts.append(f"Message directed at you: {'Yes' if is_directed else 'No'}")

            context_parts.append("")

            for msg in reversed(context_messages):  # Show in chronological order
                role = owner_name if msg.is_owner else msg.sender_name
                preview = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                context_parts.append(f"{role}: {preview}")

            context_parts.append(f"\nMessage you need to respond to:")
            context_parts.append(f"{last_non_owner.sender_name}: {last_non_owner.text}")

            # Add skip guidance based on chat type
            if chat_type == "group":
                context_parts.append(f"\nGROUP CHAT: If this message is not directed at you or you wouldn't naturally join this conversation, respond with '.skip'")
            elif chat_type == "private":
                context_parts.append(f"\nPRIVATE CHAT: If you would ignore this message or not respond (based on your style), respond with '.skip'")

            context_parts.append(f"\nRespond as {owner_name} would respond, or '.skip' if no response is needed.")

            return "\n".join(context_parts)

        except Exception as e:
            logger.warning(f"Error generating context summary: {e}")
            return f"Responding to {last_non_owner.sender_name}: {last_non_owner.text}"
    
    def _extract_owner_style(self, owner_messages: List[ChatMessage]) -> str:
        """Extract the owner's writing style from their messages.
        
        Args:
            owner_messages: Messages written by the owner
            
        Returns:
            str: Sample of owner's writing style
        """
        try:
            # Combine recent owner messages
            style_texts = []
            total_length = 0
            
            for msg in owner_messages:
                if total_length + len(msg.text) > self.max_style_sample:
                    break
                
                style_texts.append(msg.text)
                total_length += len(msg.text)
            
            if not style_texts:
                return ""
            
            return "\n".join(style_texts)
            
        except Exception as e:
            logger.warning(f"Error extracting owner style: {e}")
            return ""
