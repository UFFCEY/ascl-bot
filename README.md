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

## 🎯 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `.ascl <question>` | AI answers any question | `.ascl What's the weather like?` |
| `.ans` | Respond in your personal style | `.ans` (replies to last message) |
| `.aans` | Enable auto-answering mode | `.aans` (auto-responds to all messages) |
| `.mans` | Disable auto-answering | `.mans` (back to manual mode) |
| `.pref <settings>` | Set response preferences | `.pref no emojis, short responses` |

## ✨ Features

- 🎭 **Style Learning** - AI learns your writing style and responds exactly like you
- ⌨️ **Realistic Typing** - Shows "typing..." with human-like delays
- 🧠 **Smart Skip Logic** - Knows when NOT to respond (groups, irrelevant messages)
- 🎛️ **Custom Preferences** - Set response style per chat ("no emojis", "short answers", etc.)
- 🔒 **Privacy First** - All processing on your device, no data stored
- 📱 **Works Everywhere** - Private chats, groups, channels

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

## Prerequisites

- Python 3.8 or higher
- Telegram account
- OpenAI API account

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd TGbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get Telegram API credentials**
   - Go to https://my.telegram.org/apps
   - Create a new application
   - Note down your `API ID` and `API Hash`

4. **Get OpenAI API key**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Note down your API key

5. **Configure the bot**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file with your credentials:
   ```env
   TELEGRAM_API_ID=your_api_id_here
   TELEGRAM_API_HASH=your_api_hash_here
   TELEGRAM_PHONE=+1234567890
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

1. **Start the bot**
   ```bash
   python main.py
   ```

2. **First run authentication**
   - The bot will ask for your phone number (if not in .env)
   - Enter the verification code sent to your Telegram
   - If you have 2FA enabled, enter your password

3. **Use the bot**

   **For AI Questions:**
   - Type: `.ascl <your question>`
   - Example: `.ascl What is the capital of France?`
   - The bot will delete your message and replace it with an AI answer

   **For Style-Based Responses:**
   - Type: `.ans` in any chat where someone else has sent a message
   - The bot will analyze the last 10 messages, learn your writing style, and respond to the last non-owner message as you would
   - Perfect for continuing conversations naturally

   **For Automatic Answering:**
   - Type: `.aans` to enable automatic mode - the bot will respond to ALL incoming messages in your style
   - Type: `.mans` to disable automatic mode and return to manual control
   - Great for when you're busy but want to maintain conversations

   **For Custom Preferences:**
   - Type: `.pref no emojis, short responses` to set response style preferences
   - Type: `.pref` (empty) to clear preferences
   - Preferences apply to all style-based responses (.ans and .aans)

## Configuration

Edit the `.env` file to customize bot behavior:

```env
# Bot settings
BOT_COMMAND_PREFIX=.ascl          # Command prefix for questions (default: .ascl)
BOT_ANSWER_PREFIX=.ans            # Command prefix for style responses (default: .ans)
BOT_AUTO_ANSWER_PREFIX=.aans      # Command prefix for auto-answer mode (default: .aans)
BOT_MANUAL_ANSWER_PREFIX=.mans    # Command prefix for manual mode (default: .mans)
MAX_QUESTION_LENGTH=500           # Maximum question length
RESPONSE_TIMEOUT=30               # AI response timeout in seconds

# Chat analysis settings
CHAT_HISTORY_LIMIT=10             # Number of messages to analyze for context
MIN_OWNER_MESSAGES=3              # Minimum owner messages needed for style analysis
MAX_STYLE_SAMPLE_LENGTH=2000      # Maximum length of style sample text

# Message settings
INFO_MESSAGE_DELETE_DELAY=5       # Auto-delete info messages after N seconds

# Typing simulation settings
TYPING_SPEED_WPM=60               # Typing speed in words per minute
TYPING_MIN_DELAY=1.0              # Minimum typing delay in seconds
TYPING_MAX_DELAY=8.0              # Maximum typing delay in seconds
TYPING_VARIATION=0.3              # Speed variation factor (±30%)
TYPING_PAUSE_CHANCE=0.2           # Chance of thinking pauses

# Rate limiting
RATE_LIMIT_REQUESTS=10            # Max requests per user per period
RATE_LIMIT_PERIOD=60              # Rate limit period in seconds

# AI settings
OPENAI_MODEL=gpt-3.5-turbo        # OpenAI model to use

# Logging
LOG_LEVEL=INFO                    # Log level (DEBUG, INFO, WARNING, ERROR)
LOG_FILE=bot.log                  # Log file path
```

## Security Features

- **Owner-Only Commands**: Only you can use bot commands - others are silently blocked
- **Auto-Delete Info Messages**: Command confirmations disappear after 5 seconds
- **Rate Limiting**: Prevents spam and abuse
- **Content Filtering**: Blocks inappropriate content
- **User Blocking**: Temporarily blocks users who violate limits
- **Global Limits**: Prevents system overload
- **Secure Logging**: Privacy-conscious logging with hashed user IDs

## Troubleshooting

### Common Issues

1. **"Configuration validation failed"**
   - Check that all required fields in `.env` are filled
   - Verify API credentials are correct

2. **"AI connection test failed"**
   - Check your OpenAI API key
   - Verify you have sufficient API credits
   - Check internet connection

3. **"Failed to start Telegram client"**
   - Verify Telegram API credentials
   - Check phone number format (+1234567890)
   - Ensure you have access to the phone for verification

4. **"Rate limit exceeded"**
   - Wait for the rate limit period to reset
   - Reduce usage frequency
   - Check rate limit settings in `.env`

### Logs

Check the log file (`bot.log` by default) for detailed error information:
```bash
tail -f bot.log
```

## Safety and Privacy

- **No Data Storage**: The bot doesn't store your messages or conversations
- **Hashed User IDs**: User identifiers are hashed for privacy
- **Local Processing**: All processing happens on your machine
- **Secure Configuration**: API keys are stored in environment variables

## Limitations

- Only works with your own Telegram account (user bot, not bot account)
- Requires your device to be online and running the bot
- Subject to OpenAI API rate limits and costs
- Cannot be used in channels where you don't have message deletion rights

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This bot is for educational and personal use only. Users are responsible for:
- Complying with Telegram's Terms of Service
- Respying OpenAI's usage policies
- Following local laws and regulations
- Using the bot responsibly and ethically

The authors are not responsible for any misuse of this software.
