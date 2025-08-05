#!/usr/bin/env python3
"""
Setup script for Telegram AI Bot Client
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Set up environment configuration."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    try:
        # Copy example to .env
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def validate_config():
    """Validate configuration file."""
    try:
        from config import Config
        if Config.validate():
            print("✅ Configuration is valid")
            return True
        else:
            print("⚠️  Configuration validation failed")
            print("Please check your .env file and ensure all required fields are set")
            return False
    except Exception as e:
        print(f"⚠️  Could not validate configuration: {e}")
        print("This is normal if you haven't set up your .env file yet")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Telegram AI Bot Client...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Validate configuration (optional)
    validate_config()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your API credentials:")
    print("   - Telegram API ID and Hash (from https://my.telegram.org/apps)")
    print("   - Your phone number")
    print("   - OpenAI API key (from https://platform.openai.com/api-keys)")
    print("\n2. Run the bot:")
    print("   python main.py")
    print("\n3. Use the bot by typing in any Telegram chat:")
    print("   .ascl <your question>")
    print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()
