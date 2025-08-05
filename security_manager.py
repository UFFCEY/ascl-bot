#!/usr/bin/env python3
"""
ASCL Security Manager
Handles security, isolation, and privacy measures for multi-tenant hosting.
"""

import os
import logging
import hashlib
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import psutil
from cryptography.fernet import Fernet
import json

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security and isolation for user instances."""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.user_processes: Dict[int, Dict[str, Any]] = {}
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data."""
        key_file = Path("security/encryption.key")
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Read-only for owner
            return key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like API keys."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def create_secure_user_environment(self, user_id: int) -> Dict[str, str]:
        """Create secure isolated environment for user."""
        user_path = Path(f"user_instances/user_{user_id}")
        
        # Create directory structure with proper permissions
        directories = [
            user_path,
            user_path / "sessions",
            user_path / "logs",
            user_path / "data",
            user_path / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            os.chmod(directory, 0o700)  # Owner only
        
        # Create security manifest
        security_manifest = {
            "user_id": user_id,
            "created_at": os.time.time(),
            "permissions": {
                "network_access": True,
                "file_system_access": "restricted",
                "process_isolation": True
            },
            "resource_limits": {
                "max_memory_mb": 512,
                "max_cpu_percent": 25,
                "max_disk_mb": 1024
            }
        }
        
        manifest_file = user_path / "security_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(security_manifest, f, indent=2)
        os.chmod(manifest_file, 0o600)
        
        return {
            "user_path": str(user_path),
            "manifest_file": str(manifest_file)
        }
    
    def sanitize_user_input(self, user_input: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Remove potentially dangerous characters
        dangerous_chars = ['`', '$', '|', '&', ';', '>', '<', '(', ')', '{', '}']
        sanitized = user_input
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limit length
        return sanitized[:1000]
    
    def validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format."""
        import re
        # Basic phone number validation
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))
    
    def generate_secure_session_id(self, user_id: int) -> str:
        """Generate secure session ID."""
        random_data = secrets.token_bytes(32)
        user_data = str(user_id).encode()
        timestamp = str(int(os.time.time())).encode()
        
        combined = random_data + user_data + timestamp
        return hashlib.sha256(combined).hexdigest()
    
    def monitor_user_process(self, user_id: int, process_id: int) -> Dict[str, Any]:
        """Monitor user process for resource usage and security."""
        try:
            process = psutil.Process(process_id)
            
            # Get resource usage
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            # Check if process is still running
            is_running = process.is_running()
            
            # Get open files (for security monitoring)
            try:
                open_files = len(process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0
            
            # Get network connections
            try:
                connections = len(process.connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            monitoring_data = {
                "user_id": user_id,
                "process_id": process_id,
                "is_running": is_running,
                "memory_mb": memory_info.rss / 1024 / 1024,
                "cpu_percent": cpu_percent,
                "open_files": open_files,
                "network_connections": connections,
                "timestamp": os.time.time()
            }
            
            # Store monitoring data
            self.user_processes[user_id] = monitoring_data
            
            # Check for resource violations
            violations = self._check_resource_violations(user_id, monitoring_data)
            if violations:
                logger.warning(f"Resource violations for user {user_id}: {violations}")
            
            return monitoring_data
            
        except psutil.NoSuchProcess:
            logger.info(f"Process {process_id} for user {user_id} no longer exists")
            return {"error": "Process not found"}
        except Exception as e:
            logger.error(f"Error monitoring process for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _check_resource_violations(self, user_id: int, monitoring_data: Dict[str, Any]) -> List[str]:
        """Check for resource limit violations."""
        violations = []
        
        # Check memory limit (512 MB)
        if monitoring_data["memory_mb"] > 512:
            violations.append(f"Memory usage: {monitoring_data['memory_mb']:.1f}MB > 512MB")
        
        # Check CPU limit (25%)
        if monitoring_data["cpu_percent"] > 25:
            violations.append(f"CPU usage: {monitoring_data['cpu_percent']:.1f}% > 25%")
        
        # Check file handles (security concern)
        if monitoring_data["open_files"] > 100:
            violations.append(f"Too many open files: {monitoring_data['open_files']} > 100")
        
        # Check network connections (security concern)
        if monitoring_data["network_connections"] > 50:
            violations.append(f"Too many connections: {monitoring_data['network_connections']} > 50")
        
        return violations
    
    def cleanup_user_data(self, user_id: int, secure_delete: bool = True) -> bool:
        """Securely clean up user data."""
        try:
            user_path = Path(f"user_instances/user_{user_id}")
            
            if not user_path.exists():
                return True
            
            if secure_delete:
                # Secure deletion - overwrite files before deletion
                for file_path in user_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            # Overwrite with random data
                            file_size = file_path.stat().st_size
                            with open(file_path, 'wb') as f:
                                f.write(secrets.token_bytes(file_size))
                        except Exception as e:
                            logger.warning(f"Could not securely overwrite {file_path}: {e}")
            
            # Remove directory
            import shutil
            shutil.rmtree(user_path)
            
            # Remove from monitoring
            if user_id in self.user_processes:
                del self.user_processes[user_id]
            
            logger.info(f"Cleaned up user data for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up user data for {user_id}: {e}")
            return False
    
    def audit_user_activity(self, user_id: int) -> Dict[str, Any]:
        """Audit user activity for security purposes."""
        try:
            user_path = Path(f"user_instances/user_{user_id}")
            
            if not user_path.exists():
                return {"error": "User path not found"}
            
            # Check log files
            log_files = list((user_path / "logs").glob("*.log"))
            
            # Check session files
            session_files = list((user_path / "sessions").glob("*"))
            
            # Check data files
            data_files = list((user_path / "data").glob("*"))
            
            # Get directory size
            total_size = sum(f.stat().st_size for f in user_path.rglob("*") if f.is_file())
            
            audit_data = {
                "user_id": user_id,
                "log_files": len(log_files),
                "session_files": len(session_files),
                "data_files": len(data_files),
                "total_size_mb": total_size / 1024 / 1024,
                "last_modified": max((f.stat().st_mtime for f in user_path.rglob("*") if f.is_file()), default=0),
                "audit_timestamp": os.time.time()
            }
            
            return audit_data
            
        except Exception as e:
            logger.error(f"Error auditing user {user_id}: {e}")
            return {"error": str(e)}
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status."""
        return {
            "total_monitored_users": len(self.user_processes),
            "active_processes": sum(1 for p in self.user_processes.values() if p.get("is_running", False)),
            "total_memory_usage": sum(p.get("memory_mb", 0) for p in self.user_processes.values()),
            "encryption_enabled": True,
            "isolation_enabled": True,
            "monitoring_active": True
        }
    
    def validate_api_credentials(self, api_id: str, api_hash: str) -> bool:
        """Validate API credentials format."""
        try:
            # Basic validation
            api_id_int = int(api_id)
            if api_id_int <= 0:
                return False
            
            if not api_hash or len(api_hash) < 32:
                return False
            
            # Check for obviously fake credentials
            fake_patterns = ["your_api", "example", "test", "fake", "demo"]
            for pattern in fake_patterns:
                if pattern in api_hash.lower():
                    return False
            
            return True
            
        except ValueError:
            return False

# Global security manager instance
security_manager = SecurityManager()
