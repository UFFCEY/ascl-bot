#!/usr/bin/env python3
"""
ASCL Bot Setup Script
Automated setup for the ASCL Telegram AI client.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version}")

def install_requirements():
    """Install required packages."""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        sys.exit(1)

def check_env_file():
    """Check if .env file exists and is configured."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("Please create a .env file with your configuration.")
        print("Use .env.example as a template.")
        return False
    
    # Check if required variables are set
    required_vars = [
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH", 
        "TELEGRAM_PHONE",
        "OPENAI_API_KEY"
    ]
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your_" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or unconfigured variables in .env: {', '.join(missing_vars)}")
        return False
    
    print("✅ .env file configured")
    return True

def create_session_directory():
    """Create session directory for Telegram client."""
    session_dir = Path("sessions")
    session_dir.mkdir(exist_ok=True)
    print("✅ Session directory created")

def test_imports():
    """Test if all required modules can be imported."""
    print("🧪 Testing imports...")
    try:
        import telethon
        import openai
        import asyncio
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 ASCL Bot Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install requirements
    install_requirements()
    
    # Test imports
    if not test_imports():
        print("❌ Setup failed due to import errors")
        sys.exit(1)
    
    # Check environment configuration
    if not check_env_file():
        print("❌ Setup failed due to missing configuration")
        sys.exit(1)
    
    # Create necessary directories
    create_session_directory()
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run: python main.py")
    print("2. Follow the Telegram authentication prompts")
    print("3. Start using your ASCL bot!")
    print("\nCommands:")
    print("• .ascl <question> - Ask AI a question")
    print("• .ans - Respond in your style")
    print("• .aans - Enable auto-answering")
    print("• .mans - Disable auto-answering")
    print("• .pref <preferences> - Set response preferences")

if __name__ == "__main__":
    main()
