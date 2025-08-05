#!/usr/bin/env python3
"""
ASCL Authentication Proxy
Handles Telegram authentication through the wizard bot interface.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from session_manager import session_manager
from host_manager import host_manager

logger = logging.getLogger(__name__)

class AuthenticationProxy:
    """Proxy for handling Telegram authentication through the wizard bot."""
    
    def __init__(self):
        self.pending_auth: Dict[int, Dict[str, Any]] = {}
    
    async def start_phone_auth(self, update: Update, user_id: int, phone: str, api_id: int, api_hash: str) -> bool:
        """Start phone-based authentication."""
        try:
            # Start authentication with session manager
            result = await session_manager.start_authentication(user_id, phone, api_id, api_hash)
            
            if result["success"]:
                if result["status"] == "already_authenticated":
                    # User already authenticated, proceed to bot creation
                    await self._complete_authentication(update, user_id)
                    return True
                elif result["status"] == "code_sent":
                    # Store pending auth info
                    self.pending_auth[user_id] = {
                        "phone": phone,
                        "api_id": api_id,
                        "api_hash": api_hash,
                        "step": "code"
                    }
                    
                    # Ask for verification code
                    await self._request_verification_code(update, user_id, phone)
                    return True
            else:
                # Authentication failed
                await update.message.reply_text(f"❌ Authentication failed: {result['message']}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting phone auth for user {user_id}: {e}")
            await update.message.reply_text("❌ Authentication error. Please try again.")
            return False
    
    async def _request_verification_code(self, update: Update, user_id: int, phone: str):
        """Request verification code from user."""
        text = f"📱 Verification Code Sent\n\n"
        text += f"A verification code has been sent to {phone}\n"
        text += f"Please enter the code you received:"
        
        await update.message.reply_text(text)
    
    async def handle_verification_code(self, update: Update, user_id: int, code: str) -> bool:
        """Handle verification code input."""
        try:
            pending = self.pending_auth.get(user_id)
            if not pending or pending["step"] != "code":
                await update.message.reply_text("❌ No pending verification. Please restart setup.")
                return False
            
            # Verify code with session manager
            result = await session_manager.verify_code(user_id, code)
            
            if result["success"]:
                if result["status"] == "authenticated":
                    # Authentication successful
                    await self._complete_authentication(update, user_id)
                    return True
            elif result["status"] == "password_required":
                # Two-factor authentication required
                pending["step"] = "password"
                await self._request_2fa_password(update, user_id)
                return True
            else:
                # Code verification failed
                await update.message.reply_text(f"❌ {result['message']}\nPlease try again:")
                return False
                
        except Exception as e:
            logger.error(f"Error handling verification code for user {user_id}: {e}")
            await update.message.reply_text("❌ Verification error. Please try again.")
            return False
    
    async def _request_2fa_password(self, update: Update, user_id: int):
        """Request two-factor authentication password."""
        text = f"🔐 Two-Factor Authentication\n\n"
        text += f"Your account has two-factor authentication enabled.\n"
        text += f"Please enter your 2FA password:"
        
        await update.message.reply_text(text)
    
    async def handle_2fa_password(self, update: Update, user_id: int, password: str) -> bool:
        """Handle two-factor authentication password."""
        try:
            pending = self.pending_auth.get(user_id)
            if not pending or pending["step"] != "password":
                await update.message.reply_text("❌ No pending 2FA verification. Please restart setup.")
                return False
            
            # Verify password with session manager
            result = await session_manager.verify_password(user_id, password)
            
            if result["success"]:
                # Authentication successful
                await self._complete_authentication(update, user_id)
                return True
            else:
                # Password verification failed
                await update.message.reply_text(f"❌ {result['message']}\nPlease try again:")
                return False
                
        except Exception as e:
            logger.error(f"Error handling 2FA password for user {user_id}: {e}")
            await update.message.reply_text("❌ 2FA verification error. Please try again.")
            return False
    
    async def _complete_authentication(self, update: Update, user_id: int):
        """Complete authentication and create user instance."""
        try:
            pending = self.pending_auth.get(user_id)
            if pending:
                phone = pending["phone"]
                del self.pending_auth[user_id]
            else:
                # For already authenticated users, get phone from session
                session_status = session_manager.get_session_status(user_id)
                phone = session_status.get("phone", "unknown")
            
            # Create user instance in host manager
            success = await host_manager.create_user_instance(user_id, phone)
            
            if success:
                # Start user bot
                bot_started = await host_manager.start_user_bot(user_id)
                
                if bot_started:
                    await self._send_success_message(update, user_id, phone)
                else:
                    await update.message.reply_text("❌ Failed to start your bot. Please contact @uffcey for support.")
            else:
                await update.message.reply_text("❌ Failed to create your bot instance. Please contact @uffcey for support.")

        except Exception as e:
            logger.error(f"Error completing authentication for user {user_id}: {e}")
            await update.message.reply_text("❌ Setup completion error. Please contact @uffcey for support.")
    
    async def _send_success_message(self, update: Update, user_id: int, phone: str):
        """Send success message with bot information."""
        text = f"🎉 Setup Complete!\n\n"
        text += f"Your ASCL bot is now active and running 24/7!\n\n"
        text += f"📱 Phone: {phone}\n"
        text += f"🤖 User ID: {user_id}\n"
        text += f"⚡ Status: Active\n\n"
        text += f"🎯 Available Commands:\n"
        text += f"• .ascl <question> - Ask AI anything\n"
        text += f"• .ans - Respond in your style\n"
        text += f"• .aans - Enable auto-answering\n"
        text += f"• .mans - Disable auto-answering\n"
        text += f"• .pref <settings> - Set preferences\n\n"
        text += f"💬 Your bot is now monitoring your messages!\n"
        text += f"📞 Support: @uffcey\n📢 Updates: @luareload"

        keyboard = [
            [InlineKeyboardButton("📊 Bot Status", callback_data=f"status_{user_id}")],
            [InlineKeyboardButton("⚙️ Settings", callback_data=f"settings_{user_id}")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/uffcey")],
            [InlineKeyboardButton("📢 Channel", url="https://t.me/luareload")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def handle_status_request(self, query, user_id: int):
        """Handle bot status request."""
        try:
            status = host_manager.get_user_status(user_id)
            
            if status["exists"]:
                text = f"📊 Bot Status\n\n"
                text += f"🤖 User ID: {user_id}\n"
                text += f"📱 Phone: {status['phone']}\n"
                text += f"⚡ Status: {status['status'].title()}\n"
                text += f"🕐 Created: {self._format_timestamp(status['created_at'])}\n"
                
                if status['last_activity']:
                    text += f"🔄 Last Activity: {self._format_timestamp(status['last_activity'])}\n"
                
                if status['process_id']:
                    text += f"🔧 Process ID: {status['process_id']}\n"
                
                # Add system status
                system_status = host_manager.get_system_status()
                text += f"\n🌐 System Status:\n"
                text += f"👥 Total Users: {system_status['total_users']}\n"
                text += f"🟢 Active Bots: {system_status['active_instances']}\n"
            else:
                text = f"❌ No bot instance found for user {user_id}"
            
            await query.edit_message_text(text)
            
        except Exception as e:
            logger.error(f"Error getting status for user {user_id}: {e}")
            await query.edit_message_text("❌ Error retrieving status")
    
    async def handle_settings_request(self, query, user_id: int):
        """Handle bot settings request."""
        try:
            keyboard = [
                [InlineKeyboardButton("🔄 Restart Bot", callback_data=f"restart_{user_id}")],
                [InlineKeyboardButton("⏹️ Stop Bot", callback_data=f"stop_{user_id}")],
                [InlineKeyboardButton("🗑️ Delete Bot", callback_data=f"delete_{user_id}")],
                [InlineKeyboardButton("⬅️ Back", callback_data=f"status_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"⚙️ Bot Settings\n\n"
            text += f"Choose an action for your bot:"
            
            await query.edit_message_text(text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing settings for user {user_id}: {e}")
            await query.edit_message_text("❌ Error loading settings")
    
    async def handle_bot_action(self, query, action: str, user_id: int):
        """Handle bot management actions."""
        try:
            if action == "restart":
                await host_manager.stop_user_bot(user_id)
                success = await host_manager.start_user_bot(user_id)
                message = "✅ Bot restarted successfully" if success else "❌ Failed to restart bot"
            
            elif action == "stop":
                success = await host_manager.stop_user_bot(user_id)
                message = "⏹️ Bot stopped successfully" if success else "❌ Failed to stop bot"
            
            elif action == "delete":
                success = await host_manager.remove_user_instance(user_id)
                message = "🗑️ Bot deleted successfully" if success else "❌ Failed to delete bot"
            
            else:
                message = "❌ Unknown action"
            
            await query.edit_message_text(message)
            
        except Exception as e:
            logger.error(f"Error handling action {action} for user {user_id}: {e}")
            await query.edit_message_text("❌ Error performing action")
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display."""
        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "Unknown"
    
    def get_pending_auth_step(self, user_id: int) -> Optional[str]:
        """Get current authentication step for user."""
        pending = self.pending_auth.get(user_id)
        return pending["step"] if pending else None
    
    def clear_pending_auth(self, user_id: int):
        """Clear pending authentication for user."""
        if user_id in self.pending_auth:
            del self.pending_auth[user_id]

# Global authentication proxy instance
auth_proxy = AuthenticationProxy()
