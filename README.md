# 🤖 ASCL Bot - AI-Powered Telegram Client

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram](https://img.shields.io/badge/Setup_Wizard-@asclw__bot-blue.svg)](https://t.me/asclw_bot)
[![Support](https://img.shields.io/badge/Support-@uffcey-green.svg)](https://t.me/uffcey)
[![Channel](https://img.shields.io/badge/Channel-@luareload-red.svg)](https://t.me/luareload)

**Transform your Telegram into an AI-powered assistant that learns your style and responds like you!**

## 🚀 Quick Start

### Option 1: Instant Setup (Recommended)
1. **Message [@asclw_bot](https://t.me/asclw_bot)** on Telegram
2. **Choose "Full Hosting"** for easiest setup
3. **Enter your phone number** (that's it!)
4. **Get your AI bot in 2 minutes!**

### Option 2: Self-Hosting (Free)
1. **Clone this repository**
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Configure `.env`** with your credentials
4. **Run setup:** `python setup.py`
5. **Start bot:** `python main.py`

## ✨ Features

- 🎭 **Style Learning** - AI learns your writing style and responds exactly like you
- ⌨️ **Realistic Typing** - Shows "typing..." with human-like delays
- 🧠 **Smart Skip Logic** - Knows when NOT to respond (groups, irrelevant messages)
- 🎛️ **Custom Preferences** - Set response style per chat ("no emojis", "short answers", etc.)
- 🔒 **Privacy First** - All processing on your device, no data stored
- 📱 **Works Everywhere** - Private chats, groups, channels

## 🎯 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `.ascl <question>` | AI answers any question | `.ascl What's the weather like?` |
| `.ans` | Respond in your personal style | `.ans` (replies to last message) |
| `.aans` | Enable auto-answering mode | `.aans` (auto-responds to all messages) |
| `.mans` | Disable auto-answering | `.mans` (back to manual mode) |
| `.pref <settings>` | Set response preferences | `.pref no emojis, short responses` |

## 🎭 Example Usage

### AI Question Answering
```
You: .ascl How do I center a div in CSS?
Bot: You can center a div using flexbox: display: flex; justify-content: center; align-items: center;
```

### Style-Based Responses
```
Friend: Hey, how's your day going?
You: .ans
Bot: hey! pretty good, just working on some projects. how about you?
```

### Smart Preferences
```
You: .pref no emojis, casual tone, short responses
Friend: What do you think about the new iPhone?
Bot: its pretty good, camera is nice but expensive
```

## 💰 Pricing Options

### 🆓 **Free Self-Hosting**
- Download from GitHub
- Run on your computer
- Use your own API keys
- Full features included

### 🚀 **Full Hosting - $24.99/month**
- **No setup required** - just your phone number!
- 24/7 hosting on our servers
- OpenAI API included
- Instant activation
- Priority support

### 💎 **Premium - $39.99/month**
- Everything in Full Hosting
- Multiple accounts (up to 3)
- Advanced features
- Dedicated resources

## 🛠️ Self-Hosting Setup

### Prerequisites
- Python 3.8 or higher
- Telegram API credentials ([get here](https://my.telegram.org/apps))
- OpenAI API key ([get here](https://platform.openai.com/api-keys))

### Installation
```bash
# Clone the repository
git clone https://github.com/UFFCEY/ascl-bot.git
cd ascl-bot

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env

# Run setup
python setup.py

# Start the bot
python main.py
```

### Configuration
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

## 🧠 How It Works

### Style Learning
The bot analyzes your recent messages to learn:
- Your vocabulary and slang
- Sentence structure and length
- Emoji usage patterns
- Formality level
- Response timing

### Smart Skip Logic
In **group chats**, skips when:
- Message isn't directed at you
- You wouldn't naturally join the conversation
- Topic is irrelevant to you

In **private chats**, skips when:
- You'd typically ignore the message
- Response isn't warranted
- Matches your natural patterns

### Realistic Behavior
- **Typing delays** based on message length
- **Human-like pauses** while "thinking"
- **Natural response timing**
- **Authentic conversation flow**

## 🛡️ Security & Privacy

- **Owner-Only**: Only you can use your bot commands
- **Local Processing**: All AI processing on your device
- **No Data Storage**: Messages aren't logged or stored
- **Encrypted Sessions**: Secure Telegram authentication
- **Rate Limiting**: Prevents spam and abuse

## 🤝 Support & Community

- 🤖 **Setup Wizard**: [@asclw_bot](https://t.me/asclw_bot)
- 💬 **Support**: [@uffcey](https://t.me/uffcey)
- 📢 **Updates**: [@luareload](https://t.me/luareload)
- 🐛 **Issues**: [GitHub Issues](https://github.com/UFFCEY/ascl-bot/issues)

## 🌟 Why Choose ASCL Bot?

### ✅ **Most Realistic**
Advanced AI that truly mimics your writing style and knows when to stay silent.

### ✅ **Easiest Setup**
From 30-minute technical setup to 2-minute phone number entry.

### ✅ **Privacy Focused**
All processing happens locally. No data collection or storage.

### ✅ **Flexible Options**
Free self-hosting to premium managed service.

### ✅ **Active Development**
Regular updates and new features based on user feedback.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram client functionality
- [OpenAI](https://openai.com/) for AI capabilities
- The Telegram community for inspiration and feedback

---

**Made with ❤️ by [@luareload](https://t.me/luareload) for the Telegram community**

⭐ **Star this repo if you find it useful!**
