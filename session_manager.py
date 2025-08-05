#!/usr/bin/env python3
"""
ASCL Session Manager
Handles Telegram authentication and session management for hosted users.
"""

import asyncio
import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneNumberInvalidError
import time

logger = logging.getLogger(__name__)

@dataclass
class AuthSession:
    """Authentication session data."""
    user_id: int
    phone: str
    api_id: int
    api_hash: str
    session_file: str
    status: str = "pending"  # pending, code_sent, authenticated, error
    code_hash: Optional[str] = None
    created_at: float = 0
    expires_at: float = 0

class TelegramSessionManager:
    """Manages Telegram authentication sessions for multiple users."""
    
    def __init__(self):
        self.active_sessions: Dict[int, AuthSession] = {}
        self.authenticated_clients: Dict[int, TelegramClient] = {}
    
    async def start_authentication(self, user_id: int, phone: str, api_id: int, api_hash: str) -> Dict[str, Any]:
        """Start Telegram authentication process."""
        try:
            # Create session file path
            session_dir = Path(f"user_instances/user_{user_id}/sessions")
            session_dir.mkdir(parents=True, exist_ok=True)
            session_file = str(session_dir / "telegram_session")
            
            # Create Telegram client
            client = TelegramClient(session_file, api_id, api_hash)
            
            # Connect to Telegram
            await client.connect()
            
            # Check if already authenticated
            if await client.is_user_authorized():
                logger.info(f"User {user_id} already authenticated")
                self.authenticated_clients[user_id] = client
                return {
                    "success": True,
                    "status": "already_authenticated",
                    "message": "User is already authenticated"
                }
            
            # Send code request
            sent_code = await client.send_code_request(phone)
            
            # Create auth session
            auth_session = AuthSession(
                user_id=user_id,
                phone=phone,
                api_id=api_id,
                api_hash=api_hash,
                session_file=session_file,
                status="code_sent",
                code_hash=sent_code.phone_code_hash,
                created_at=time.time(),
                expires_at=time.time() + 300  # 5 minutes
            )
            
            self.active_sessions[user_id] = auth_session
            
            # Store client temporarily
            self.authenticated_clients[user_id] = client
            
            logger.info(f"Code sent to {phone} for user {user_id}")
            
            return {
                "success": True,
                "status": "code_sent",
                "message": f"Verification code sent to {phone}",
                "phone": phone
            }
            
        except PhoneNumberInvalidError:
            logger.error(f"Invalid phone number: {phone}")
            return {
                "success": False,
                "status": "error",
                "message": "Invalid phone number format"
            }
        except Exception as e:
            logger.error(f"Error starting authentication for {user_id}: {e}")
            return {
                "success": False,
                "status": "error",
                "message": f"Authentication error: {str(e)}"
            }
    
    async def verify_code(self, user_id: int, code: str) -> Dict[str, Any]:
        """Verify SMS code and complete authentication."""
        try:
            auth_session = self.active_sessions.get(user_id)
            if not auth_session:
                return {
                    "success": False,
                    "status": "error",
                    "message": "No active authentication session"
                }
            
            # Check if session expired
            if time.time() > auth_session.expires_at:
                del self.active_sessions[user_id]
                return {
                    "success": False,
                    "status": "error",
                    "message": "Authentication session expired"
                }
            
            client = self.authenticated_clients.get(user_id)
            if not client:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Client not found"
                }
            
            # Verify the code
            try:
                await client.sign_in(auth_session.phone, code, phone_code_hash=auth_session.code_hash)
                
                # Update session status
                auth_session.status = "authenticated"
                
                logger.info(f"User {user_id} authenticated successfully")
                
                return {
                    "success": True,
                    "status": "authenticated",
                    "message": "Authentication successful"
                }
                
            except SessionPasswordNeededError:
                # Two-factor authentication required
                auth_session.status = "password_required"
                return {
                    "success": False,
                    "status": "password_required",
                    "message": "Two-factor authentication password required"
                }
            except PhoneCodeInvalidError:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Invalid verification code"
                }
                
        except Exception as e:
            logger.error(f"Error verifying code for user {user_id}: {e}")
            return {
                "success": False,
                "status": "error",
                "message": f"Verification error: {str(e)}"
            }
    
    async def verify_password(self, user_id: int, password: str) -> Dict[str, Any]:
        """Verify two-factor authentication password."""
        try:
            auth_session = self.active_sessions.get(user_id)
            if not auth_session or auth_session.status != "password_required":
                return {
                    "success": False,
                    "status": "error",
                    "message": "No password verification required"
                }
            
            client = self.authenticated_clients.get(user_id)
            if not client:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Client not found"
                }
            
            # Verify password
            await client.sign_in(password=password)
            
            # Update session status
            auth_session.status = "authenticated"
            
            logger.info(f"User {user_id} authenticated with 2FA")
            
            return {
                "success": True,
                "status": "authenticated",
                "message": "Two-factor authentication successful"
            }
            
        except Exception as e:
            logger.error(f"Error verifying password for user {user_id}: {e}")
            return {
                "success": False,
                "status": "error",
                "message": f"Password verification error: {str(e)}"
            }
    
    async def get_authenticated_client(self, user_id: int) -> Optional[TelegramClient]:
        """Get authenticated Telegram client for user."""
        auth_session = self.active_sessions.get(user_id)
        if auth_session and auth_session.status == "authenticated":
            return self.authenticated_clients.get(user_id)
        return None
    
    async def disconnect_user(self, user_id: int) -> bool:
        """Disconnect user session."""
        try:
            client = self.authenticated_clients.get(user_id)
            if client:
                await client.disconnect()
                del self.authenticated_clients[user_id]
            
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
            
            logger.info(f"Disconnected user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id}: {e}")
            return False
    
    def get_session_status(self, user_id: int) -> Dict[str, Any]:
        """Get authentication session status."""
        auth_session = self.active_sessions.get(user_id)
        if not auth_session:
            return {
                "exists": False,
                "status": "no_session"
            }
        
        return {
            "exists": True,
            "status": auth_session.status,
            "phone": auth_session.phone,
            "created_at": auth_session.created_at,
            "expires_at": auth_session.expires_at,
            "time_remaining": max(0, auth_session.expires_at - time.time())
        }
    
    async def cleanup_expired_sessions(self):
        """Clean up expired authentication sessions."""
        current_time = time.time()
        expired_users = []
        
        for user_id, session in self.active_sessions.items():
            if current_time > session.expires_at and session.status != "authenticated":
                expired_users.append(user_id)
        
        for user_id in expired_users:
            await self.disconnect_user(user_id)
            logger.info(f"Cleaned up expired session for user {user_id}")
    
    async def load_existing_sessions(self):
        """Load existing authenticated sessions on startup."""
        try:
            user_instances_dir = Path("user_instances")
            if not user_instances_dir.exists():
                return
            
            for user_dir in user_instances_dir.iterdir():
                if not user_dir.is_dir() or not user_dir.name.startswith("user_"):
                    continue
                
                try:
                    user_id = int(user_dir.name.split("_")[1])
                    session_file = user_dir / "sessions" / "telegram_session.session"
                    
                    if session_file.exists():
                        # Try to load existing session
                        config_file = user_dir / ".env"
                        if config_file.exists():
                            # Parse config to get API credentials
                            config = {}
                            with open(config_file, 'r') as f:
                                for line in f:
                                    if '=' in line and not line.startswith('#'):
                                        key, value = line.strip().split('=', 1)
                                        config[key] = value
                            
                            api_id = int(config.get('TELEGRAM_API_ID', 0))
                            api_hash = config.get('TELEGRAM_API_HASH', '')
                            phone = config.get('TELEGRAM_PHONE', '')
                            
                            if api_id and api_hash:
                                # Create client and check if authenticated
                                client = TelegramClient(str(session_file).replace('.session', ''), api_id, api_hash)
                                await client.connect()
                                
                                if await client.is_user_authorized():
                                    self.authenticated_clients[user_id] = client
                                    
                                    # Create auth session record
                                    auth_session = AuthSession(
                                        user_id=user_id,
                                        phone=phone,
                                        api_id=api_id,
                                        api_hash=api_hash,
                                        session_file=str(session_file).replace('.session', ''),
                                        status="authenticated",
                                        created_at=time.time()
                                    )
                                    self.active_sessions[user_id] = auth_session
                                    
                                    logger.info(f"Loaded existing session for user {user_id}")
                                else:
                                    await client.disconnect()
                
                except Exception as e:
                    logger.warning(f"Error loading session for {user_dir.name}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error loading existing sessions: {e}")

# Global session manager instance
session_manager = TelegramSessionManager()
