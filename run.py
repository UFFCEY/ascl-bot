#!/usr/bin/env python3
"""
Simple launcher script for Telegram AI Bot Client
"""

import sys
import os
import subprocess
from pathlib import Path

def check_setup():
    """Check if the bot is properly set up."""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ required (current: {sys.version})")
    
    # Check if dependencies are installed
    try:
        import telethon
        import openai
        import dotenv
    except ImportError as e:
        issues.append(f"Missing dependency: {e.name}")
        issues.append("Run: python setup.py")
    
    # Check if .env file exists
    if not Path(".env").exists():
        issues.append(".env file not found")
        issues.append("Run: python setup.py")
    
    # Check configuration
    try:
        from config import Config
        if not Config.validate():
            issues.append("Configuration incomplete")
            issues.append("Edit .env file with your API credentials")
    except Exception as e:
        issues.append(f"Configuration error: {e}")
    
    return issues

def main():
    """Main launcher function."""
    print("🤖 Telegram AI Bot Client Launcher")
    print("=" * 40)
    
    # Check setup
    issues = check_setup()
    if issues:
        print("❌ Setup issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nPlease fix these issues before running the bot.")
        return False
    
    print("✅ Setup looks good!")
    print("🚀 Starting bot...\n")
    
    # Run the bot
    try:
        from main import main as bot_main
        import asyncio
        asyncio.run(bot_main())
        return True
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Error running bot: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
