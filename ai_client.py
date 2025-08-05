import asyncio
import openai
from typing import Optional, Dict, Any
from dataclasses import dataclass
from config import Config
from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class AIResponse:
    """Represents a response from the AI model."""
    success: bool
    response_text: str
    should_skip: bool = False  # True if AI decided to skip responding
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None

class AIClient:
    """Client for interacting with AI models to generate responses."""
    
    def __init__(self):
        """Initialize the AI client."""
        self.client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.timeout = Config.RESPONSE_TIMEOUT
        
        # System prompts for different modes
        self.question_prompt = """You are a helpful AI assistant integrated into a Telegram chat.
You should provide clear, concise, and helpful responses to questions.
Keep your responses conversational and appropriate for a chat environment.
If you're unsure about something, it's okay to say so.
Avoid overly long responses unless specifically requested."""

        self.style_prompt = """You are responding as the user in a Telegram chat. Your task is to respond to the last message in the conversation exactly as the user would respond, using their personal writing style.

CRITICAL INSTRUCTIONS:
1. You are responding AS THE USER, not as an AI assistant
2. Analyze the user's writing style from their previous messages carefully
3. Match their exact tone, vocabulary, slang, and communication patterns
4. Use their typical sentence structure and length
5. Mirror their level of formality/informality
6. Copy their use of emojis, punctuation, and capitalization
7. Respond naturally as if you ARE the user
8. Never mention that you're an AI or that you're mimicking someone
9. Be completely authentic to the user's personality and style
10. The response should sound like it came directly from the user
11. IMPORTANT: Only provide the message text, do NOT include the sender name or any prefix like "User:" or "liminal AX400:"

SKIP LOGIC - VERY IMPORTANT:
12. If you determine that the user would NOT respond to this message, write ONLY ".skip" (nothing else)
13. In GROUP CHATS: Skip if the message is not directed at the user, is irrelevant to them, or they wouldn't naturally join the conversation
14. In PRIVATE CHATS: Skip if it would be the user's style to ignore the message (e.g., if they're busy, annoyed, or the message doesn't warrant a response)
15. Consider the user's personality - some people respond to everything, others are more selective
16. Look at conversation flow - if the user typically doesn't respond to certain types of messages, skip them

Focus on being the user, not helping them. Respond with ONLY the message content OR ".skip"."""
    
    async def generate_response(self, question: str, context: Optional[Dict[str, Any]] = None) -> AIResponse:
        """Generate a response to a question using the AI model.

        Args:
            question: The question to answer
            context: Optional context information (chat info, user info, etc.)

        Returns:
            AIResponse: The generated response or error information
        """
        return await self._generate_response_internal(question, context, "question")

    async def generate_style_response(self, chat_context: str, owner_style: str, context: Optional[Dict[str, Any]] = None, preferences: Optional[str] = None) -> AIResponse:
        """Generate a response in the owner's style based on chat context.

        Args:
            chat_context: Context of the conversation
            owner_style: Sample of owner's writing style
            context: Optional additional context information
            preferences: Optional user preferences for response style

        Returns:
            AIResponse: The generated response or error information
        """
        return await self._generate_response_internal(chat_context, context, "style", owner_style, preferences)

    async def _generate_response_internal(self, input_text: str, context: Optional[Dict[str, Any]], mode: str, owner_style: Optional[str] = None, preferences: Optional[str] = None) -> AIResponse:
        """Internal method to generate responses for different modes.

        Args:
            input_text: The input text (question or chat context)
            context: Optional context information
            mode: "question" or "style"
            owner_style: Owner's writing style sample (for style mode)
            preferences: Optional user preferences for response style

        Returns:
            AIResponse: The generated response or error information
        """
        try:
            if mode == "question":
                logger.info(f"Generating response for question: {input_text[:50]}...")
                system_prompt = self.question_prompt
                user_content = input_text
            else:  # style mode
                logger.info("Generating style-based response...")
                system_prompt = self.style_prompt

                # Build user content with preferences if provided
                user_content_parts = [
                    f"Conversation context:\n{input_text}",
                    f"\nYour writing style examples:\n{owner_style}"
                ]

                if preferences:
                    user_content_parts.append(f"\nAdditional preferences: {preferences}")

                user_content_parts.append("\nPlease respond to the last message in your natural style. Provide ONLY the message text without any name prefix.")

                user_content = "".join(user_content_parts)

            # Prepare messages for the API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

            # Add context if provided
            if context:
                context_info = self._format_context(context)
                if context_info:
                    messages.insert(1, {"role": "system", "content": context_info})
            
            # Adjust parameters based on mode
            if mode == "style":
                # For style mimicking, use higher temperature for more personality
                temperature = 0.8
                max_tokens = 800
            else:
                # For questions, use balanced settings
                temperature = 0.7
                max_tokens = 1000

            # Make API call with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    frequency_penalty=0.1,
                    presence_penalty=0.1
                ),
                timeout=self.timeout
            )
            
            # Extract response
            response_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else None

            # Check if AI decided to skip responding
            should_skip = False
            if mode == "style" and response_text.strip().lower() == ".skip":
                should_skip = True
                logger.info("AI decided to skip responding")

            # Clean up any name prefixes that might have been included (but not for skip responses)
            if mode == "style" and not should_skip:
                response_text = self._clean_response_text(response_text)

            logger.info(f"Successfully generated response ({tokens_used} tokens)")

            return AIResponse(
                success=True,
                response_text=response_text,
                should_skip=should_skip,
                tokens_used=tokens_used,
                model_used=self.model
            )
            
        except asyncio.TimeoutError:
            error_msg = f"AI response timed out after {self.timeout} seconds"
            logger.error(error_msg)
            return AIResponse(
                success=False,
                response_text="",
                error_message=error_msg
            )
            
        except openai.RateLimitError:
            error_msg = "AI API rate limit exceeded"
            logger.error(error_msg)
            return AIResponse(
                success=False,
                response_text="",
                error_message=error_msg
            )
            
        except openai.APIError as e:
            error_msg = f"AI API error: {str(e)}"
            logger.error(error_msg)
            return AIResponse(
                success=False,
                response_text="",
                error_message=error_msg
            )
            
        except Exception as e:
            error_msg = f"Unexpected error generating AI response: {str(e)}"
            logger.error(error_msg)
            return AIResponse(
                success=False,
                response_text="",
                error_message=error_msg
            )
    
    def _format_context(self, context: Dict[str, Any]) -> Optional[str]:
        """Format context information for the AI model.
        
        Args:
            context: Context dictionary
            
        Returns:
            Optional[str]: Formatted context string or None
        """
        try:
            context_parts = []
            
            if context.get('chat_title'):
                context_parts.append(f"Chat: {context['chat_title']}")
            
            if context.get('chat_type'):
                context_parts.append(f"Type: {context['chat_type']}")
            
            if context.get('user_name'):
                context_parts.append(f"User: {context['user_name']}")
            
            if context_parts:
                return "Context: " + " | ".join(context_parts)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error formatting context: {e}")
            return None
    
    def _clean_response_text(self, response_text: str) -> str:
        """Clean response text to remove any name prefixes.

        Args:
            response_text: Raw response from AI

        Returns:
            str: Cleaned response text
        """
        import re

        # Remove common name prefixes that might appear
        patterns = [
            r'^[^:]+:\s*',  # Any text followed by colon and space
            r'^liminal\s+AX400:\s*',  # Specific user name
            r'^liminal:\s*',  # Short version
            r'^AX400:\s*',  # Partial name
            r'^\w+\s*\w*:\s*',  # General name pattern
        ]

        cleaned = response_text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    async def test_connection(self) -> bool:
        """Test the connection to the AI service.

        Returns:
            bool: True if connection is working, False otherwise
        """
        try:
            test_response = await self.generate_response("Hello, this is a test.")
            return test_response.success
        except Exception as e:
            logger.error(f"AI connection test failed: {e}")
            return False
