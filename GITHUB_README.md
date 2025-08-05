# ASCL Bot - AI-Powered Telegram Client

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram](https://img.shields.io/badge/Telegram-@asclw_bot-blue.svg)](https://t.me/asclw_bot)

A powerful Telegram bot client that monitors your messages and provides AI-powered features with realistic human-like behavior.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
1. Message [@asclw_bot](https://t.me/asclw_bot) on Telegram
2. Follow the setup wizard
3. Get your configured bot instantly!

### Option 2: Manual Setup
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your `.env` file (see below)
4. Run setup: `python github_setup.py`
5. Start the bot: `python main.py`

## ✨ Features

- 🎭 **Style Mimicking**: Learns your writing style and responds as you would
- ⌨️ **Realistic Typing**: Shows "typing..." animation with human-like delays
- 🧠 **Smart Skip Logic**: AI decides when NOT to respond (groups, irrelevant messages)
- 🎛️ **Custom Preferences**: Set response style preferences per chat
- 🔒 **Security**: Rate limiting, content filtering, and abuse prevention
- 📱 **Seamless**: Works in any Telegram chat (private, groups, channels)
- 🛡️ **Safe**: Comprehensive error handling and logging
- ⚡ **Smart Timing**: Realistic response delays based on message length

## 🎯 Commands

1. **`.ascl <question>`** - Replaces your message with an AI-generated answer
2. **`.ans`** - Responds to the last message in your personal writing style
3. **`.aans`** - Enables automatic answering mode (responds to all messages)
4. **`.mans`** - Disables automatic answering mode
5. **`.pref <preferences>`** - Set custom response preferences

## 📋 Requirements

- Python 3.8 or higher
- Telegram API credentials (from https://my.telegram.org/apps)
- OpenAI API key (from https://platform.openai.com/api-keys)

## ⚙️ Configuration

Create a `.env` file with your credentials:

```env
# Telegram API Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Bot Configuration (Optional)
BOT_COMMAND_PREFIX=.ascl
BOT_ANSWER_PREFIX=.ans
BOT_AUTO_ANSWER_PREFIX=.aans
BOT_MANUAL_ANSWER_PREFIX=.mans
BOT_PREFERENCE_PREFIX=.pref
```

## 🔧 Installation

### Prerequisites
```bash
# Install Python 3.8+ from https://python.org
# Clone the repository
git clone https://github.com/yourusername/ascl-bot.git
cd ascl-bot
```

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure your .env file (see Configuration section)
cp .env.example .env
# Edit .env with your credentials

# Run setup script
python github_setup.py

# Start the bot
python main.py
```

## 🎭 Usage Examples

### Basic Question Answering
```
You: .ascl What's the weather like today?
Bot: I don't have access to real-time weather data, but you can check...
```

### Style-Based Responses
```
Friend: Hey, how are you doing?
You: .ans
Bot: hey! doing great, just working on some projects. how about you?
```

### Custom Preferences
```
You: .pref no emojis, short responses, casual tone
Bot: ✅ Preferences set: no emojis, short responses, casual tone

Friend: What do you think about the new movie?
You: .ans
Bot: its pretty good, worth watching
```

## 🧠 Smart Features

### Intelligent Skip Logic
The bot intelligently decides when to respond:

**In Groups:**
- Skips messages not directed at you
- Only responds when you'd naturally join the conversation

**In Private Chats:**
- Mimics your response patterns
- Skips when you'd typically ignore messages

### Realistic Behavior
- Human-like typing delays
- Authentic response timing
- Natural conversation flow

## 🛡️ Security & Privacy

- **Owner-only**: Only you can use the bot commands
- **Local processing**: All data stays on your device
- **No data storage**: Messages aren't logged or stored
- **Rate limiting**: Prevents spam and abuse
- **Content filtering**: Blocks inappropriate requests

## 📚 Documentation

- [Setup Guide](docs/setup.md)
- [Configuration Options](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)
- [API Reference](docs/api.md)

## 🤝 Support

- 🤖 Setup Wizard: [@asclw_bot](https://t.me/asclw_bot)
- 💬 Support Chat: [@ascl_support](https://t.me/ascl_support)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/ascl-bot/issues)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram client functionality
- [OpenAI](https://openai.com/) for AI capabilities
- The Telegram community for inspiration and feedback

---

**Made with ❤️ for the Telegram community**
