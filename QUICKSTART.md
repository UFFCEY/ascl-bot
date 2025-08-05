# Quick Start Guide

Get your Telegram AI Bot running in 5 minutes!

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
python setup.py
```

### 2. Get API Credentials

**Telegram API:**
1. Go to https://my.telegram.org/apps
2. Create new application
3. Copy API ID and API Hash

**OpenAI API:**
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Copy the key

### 3. Configure Bot
Edit `.env` file:
```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
OPENAI_API_KEY=your_openai_key
```

### 4. Run Bot
```bash
python run.py
```

### 5. Use Bot

**For AI Questions:**
```
.ascl What is the weather like today?
```

**For Style-Based Responses:**
```
.ans
```
(Use this in chats where someone else has messaged you)

**For Automatic Mode:**
```
.aans    # Enable auto-answering
.mans    # Disable auto-answering
```

The bot will replace your message with an appropriate AI response!

## 🔧 Troubleshooting

**"Configuration validation failed"**
- Check all fields in `.env` are filled
- Verify API credentials are correct

**"AI connection test failed"**
- Check OpenAI API key
- Verify you have API credits

**"Failed to start Telegram client"**
- Check Telegram API credentials
- Verify phone number format

## 📱 Usage Examples

**AI Questions:**
```
.ascl How do I cook pasta?
.ascl What is quantum computing?
.ascl Translate "hello" to Spanish
.ascl Write a short poem about cats
```

**Style-Based Responses:**
```
.ans
```
Use this when someone messages you and you want to respond in your natural style.

**Automatic Mode:**
```
.aans    # Start auto-answering all messages
.mans    # Stop auto-answering
```
Perfect for when you're busy but want to maintain conversations.

The bot will:
- Analyze your recent messages to learn your writing style
- Look at the conversation context
- Respond to messages as you would

## ⚙️ Customization

Edit `.env` to customize:
- `BOT_COMMAND_PREFIX=.ai` - Change question command prefix
- `BOT_ANSWER_PREFIX=.reply` - Change style response command prefix
- `MAX_QUESTION_LENGTH=1000` - Increase question limit
- `CHAT_HISTORY_LIMIT=15` - Analyze more messages for context
- `MIN_OWNER_MESSAGES=5` - Require more messages for style learning
- `OPENAI_MODEL=gpt-4` - Use different AI model

## 🛡️ Security & Features

- Rate limited (10 requests/minute per user)
- Content filtering for inappropriate questions
- No data storage or logging of personal information
- All processing happens locally
- Owner-only commands (others can't use your bot)
- Auto-deleting info messages (disappear after 5 seconds)
- Realistic typing simulation (shows "typing..." with human-like delays)

## 📞 Support

Check `bot.log` for detailed error information:
```bash
tail -f bot.log
```

For more details, see [README.md](README.md)
