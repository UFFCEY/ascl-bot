#!/usr/bin/env python3
"""
ASCL Host Manager
Multi-tenant system for managing multiple user ASCL instances on a single host.
"""

import asyncio
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import subprocess
import signal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class APICredential:
    """Telegram API credential set."""
    api_id: int
    api_hash: str
    app_name: str
    in_use: int = 0
    max_users: int = 100
    created_at: float = 0
    last_used: float = 0

@dataclass
class UserInstance:
    """User bot instance information."""
    user_id: int
    phone: str
    api_credential: APICredential
    process_id: Optional[int] = None
    status: str = "inactive"  # inactive, starting, active, error
    created_at: float = 0
    last_activity: float = 0
    session_path: str = ""
    config_path: str = ""

class APICredentialPool:
    """Manages pool of Telegram API credentials."""
    
    def __init__(self, credentials_file: str = "api_credentials.json"):
        self.credentials_file = Path(credentials_file)
        self.credentials: List[APICredential] = []
        self.load_credentials()
    
    def load_credentials(self):
        """Load API credentials from file."""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    data = json.load(f)
                
                self.credentials = [
                    APICredential(**cred) for cred in data.get('credentials', [])
                ]
                logger.info(f"Loaded {len(self.credentials)} API credential sets")
            else:
                # Create default credentials file
                self.create_default_credentials()
        except Exception as e:
            logger.error(f"Error loading API credentials: {e}")
            self.credentials = []
    
    def create_default_credentials(self):
        """Create default API credentials file."""
        default_creds = {
            "credentials": [
                {
                    "api_id": 12345,  # Replace with real API ID
                    "api_hash": "your_api_hash_here",  # Replace with real API hash
                    "app_name": "ASCL_App_1",
                    "max_users": 100
                }
            ]
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(default_creds, f, indent=2)
        
        logger.info("Created default API credentials file - please update with real credentials")
    
    def get_available_credential(self) -> Optional[APICredential]:
        """Get least used available API credential."""
        available = [cred for cred in self.credentials if cred.in_use < cred.max_users]
        if not available:
            return None
        
        # Return least used credential
        return min(available, key=lambda x: x.in_use)
    
    def allocate_credential(self, credential: APICredential) -> bool:
        """Allocate a credential to a user."""
        if credential.in_use >= credential.max_users:
            return False
        
        credential.in_use += 1
        credential.last_used = datetime.now().timestamp()
        self.save_credentials()
        return True
    
    def release_credential(self, credential: APICredential) -> bool:
        """Release a credential from a user."""
        if credential.in_use > 0:
            credential.in_use -= 1
            self.save_credentials()
            return True
        return False
    
    def save_credentials(self):
        """Save credentials to file."""
        try:
            data = {
                "credentials": [asdict(cred) for cred in self.credentials]
            }
            with open(self.credentials_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving API credentials: {e}")

class UserIsolator:
    """Handles user environment isolation."""
    
    def __init__(self, base_path: str = "user_instances"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def create_user_environment(self, user_id: int) -> Path:
        """Create isolated environment for user."""
        user_path = self.base_path / f"user_{user_id}"
        user_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (user_path / "sessions").mkdir(exist_ok=True)
        (user_path / "logs").mkdir(exist_ok=True)
        (user_path / "data").mkdir(exist_ok=True)
        
        logger.info(f"Created user environment: {user_path}")
        return user_path
    
    def create_user_config(self, user_id: int, phone: str, api_cred: APICredential, openai_key: str = "SERVICE_PROVIDED") -> str:
        """Create user configuration file."""
        user_path = self.create_user_environment(user_id)
        config_path = user_path / ".env"
        
        config_content = f"""# ASCL Bot Configuration for User {user_id}
# Generated automatically by Host Manager

# Telegram API Configuration
TELEGRAM_API_ID={api_cred.api_id}
TELEGRAM_API_HASH={api_cred.api_hash}
TELEGRAM_PHONE={phone}

# OpenAI Configuration
OPENAI_API_KEY={openai_key}

# Bot Configuration
BOT_COMMAND_PREFIX=.ascl
BOT_ANSWER_PREFIX=.ans
BOT_AUTO_ANSWER_PREFIX=.aans
BOT_MANUAL_ANSWER_PREFIX=.mans
BOT_PREFERENCE_PREFIX=.pref

# Paths
SESSION_PATH={user_path}/sessions/
LOG_PATH={user_path}/logs/
DATA_PATH={user_path}/data/

# Host Configuration
USER_ID={user_id}
ISOLATED_MODE=true
"""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        logger.info(f"Created user config: {config_path}")
        return str(config_path)

class HostManager:
    """Main host manager for multi-tenant ASCL instances."""
    
    def __init__(self):
        self.api_pool = APICredentialPool()
        self.user_isolator = UserIsolator()
        self.user_instances: Dict[int, UserInstance] = {}
        self.load_user_instances()
    
    def load_user_instances(self):
        """Load existing user instances."""
        instances_file = Path("user_instances.json")
        if instances_file.exists():
            try:
                with open(instances_file, 'r') as f:
                    data = json.load(f)
                
                for user_data in data.get('instances', []):
                    user_id = user_data['user_id']
                    # Reconstruct API credential
                    api_cred_data = user_data['api_credential']
                    api_cred = APICredential(**api_cred_data)
                    
                    # Create user instance
                    instance = UserInstance(
                        user_id=user_id,
                        phone=user_data['phone'],
                        api_credential=api_cred,
                        status="inactive",
                        created_at=user_data.get('created_at', 0),
                        session_path=user_data.get('session_path', ''),
                        config_path=user_data.get('config_path', '')
                    )
                    
                    self.user_instances[user_id] = instance
                
                logger.info(f"Loaded {len(self.user_instances)} user instances")
            except Exception as e:
                logger.error(f"Error loading user instances: {e}")
    
    def save_user_instances(self):
        """Save user instances to file."""
        try:
            data = {
                "instances": []
            }
            
            for instance in self.user_instances.values():
                instance_data = asdict(instance)
                data["instances"].append(instance_data)
            
            with open("user_instances.json", 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user instances: {e}")
    
    async def create_user_instance(self, user_id: int, phone: str, openai_key: str = "SERVICE_PROVIDED") -> bool:
        """Create new user instance."""
        try:
            # Check if user already exists
            if user_id in self.user_instances:
                logger.warning(f"User {user_id} already has an instance")
                return False
            
            # Get available API credential
            api_cred = self.api_pool.get_available_credential()
            if not api_cred:
                logger.error("No available API credentials")
                return False
            
            # Allocate credential
            if not self.api_pool.allocate_credential(api_cred):
                logger.error("Failed to allocate API credential")
                return False
            
            # Create user environment and config
            config_path = self.user_isolator.create_user_config(user_id, phone, api_cred, openai_key)
            
            # Create user instance
            instance = UserInstance(
                user_id=user_id,
                phone=phone,
                api_credential=api_cred,
                status="inactive",
                created_at=datetime.now().timestamp(),
                config_path=config_path,
                session_path=str(self.user_isolator.base_path / f"user_{user_id}" / "sessions")
            )
            
            self.user_instances[user_id] = instance
            self.save_user_instances()
            
            logger.info(f"Created user instance for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user instance for {user_id}: {e}")
            return False
    
    async def start_user_bot(self, user_id: int) -> bool:
        """Start bot for specific user."""
        try:
            instance = self.user_instances.get(user_id)
            if not instance:
                logger.error(f"No instance found for user {user_id}")
                return False
            
            if instance.status == "active":
                logger.info(f"Bot already active for user {user_id}")
                return True
            
            # Start bot process
            user_path = self.user_isolator.base_path / f"user_{user_id}"
            
            # Copy main bot files to user directory
            await self._copy_bot_files(user_path)
            
            # Start bot process
            process = await asyncio.create_subprocess_exec(
                "python", "main.py",
                cwd=str(user_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            instance.process_id = process.pid
            instance.status = "active"
            instance.last_activity = datetime.now().timestamp()
            
            self.save_user_instances()
            
            logger.info(f"Started bot for user {user_id} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Error starting bot for user {user_id}: {e}")
            return False
    
    async def _copy_bot_files(self, user_path: Path):
        """Copy bot files to user directory."""
        import shutil
        
        # List of files to copy
        bot_files = [
            "main.py", "config.py", "ai_client.py", "telegram_client.py",
            "message_handler.py", "message_parser.py", "chat_analyzer.py",
            "auto_response_manager.py", "typing_simulator.py", "preference_manager.py",
            "logger.py", "requirements.txt"
        ]
        
        for file_name in bot_files:
            src = Path(file_name)
            if src.exists():
                dst = user_path / file_name
                shutil.copy2(src, dst)
    
    async def stop_user_bot(self, user_id: int) -> bool:
        """Stop bot for specific user."""
        try:
            instance = self.user_instances.get(user_id)
            if not instance or instance.status != "active":
                return True
            
            if instance.process_id:
                try:
                    os.kill(instance.process_id, signal.SIGTERM)
                    logger.info(f"Stopped bot for user {user_id}")
                except ProcessLookupError:
                    logger.warning(f"Process {instance.process_id} not found")
            
            instance.status = "inactive"
            instance.process_id = None
            self.save_user_instances()
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping bot for user {user_id}: {e}")
            return False
    
    async def remove_user_instance(self, user_id: int) -> bool:
        """Remove user instance completely."""
        try:
            # Stop bot first
            await self.stop_user_bot(user_id)
            
            instance = self.user_instances.get(user_id)
            if instance:
                # Release API credential
                self.api_pool.release_credential(instance.api_credential)
                
                # Remove from instances
                del self.user_instances[user_id]
                self.save_user_instances()
            
            # Remove user directory
            user_path = self.user_isolator.base_path / f"user_{user_id}"
            if user_path.exists():
                import shutil
                shutil.rmtree(user_path)
            
            logger.info(f"Removed user instance for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing user instance for {user_id}: {e}")
            return False
    
    def get_user_status(self, user_id: int) -> Dict[str, Any]:
        """Get status of user instance."""
        instance = self.user_instances.get(user_id)
        if not instance:
            return {"exists": False}
        
        return {
            "exists": True,
            "status": instance.status,
            "phone": instance.phone,
            "created_at": instance.created_at,
            "last_activity": instance.last_activity,
            "process_id": instance.process_id
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        active_instances = sum(1 for i in self.user_instances.values() if i.status == "active")
        total_api_usage = sum(cred.in_use for cred in self.api_pool.credentials)
        
        return {
            "total_users": len(self.user_instances),
            "active_instances": active_instances,
            "api_credentials": len(self.api_pool.credentials),
            "api_usage": total_api_usage,
            "system_uptime": datetime.now().timestamp()
        }

# Global host manager instance
host_manager = HostManager()
