#!/usr/bin/env python3
"""
ASCL Bot Setup Wizard
A Telegram bot that helps users set up their own ASCL client.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import os
from dataclasses import dataclass, asdict

# Bot configuration
BOT_TOKEN = "7572173424:AAFJjSU4Vb0R4lBwhZzKTa0F1gqj0Sm6Vjs"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass
class UserSetup:
    """User setup configuration."""
    user_id: int
    language: str = "en"
    setup_type: str = ""  # "auto" or "manual"
    hosting_type: str = ""  # "personal" or "server"
    api_key_type: str = ""  # "personal" or "service"
    telegram_api_id: str = ""
    telegram_api_hash: str = ""
    telegram_phone: str = ""
    openai_api_key: str = ""
    step: str = "start"
    completed: bool = False

class SetupWizard:
    """Main setup wizard class."""
    
    def __init__(self):
        self.user_setups: Dict[int, UserSetup] = {}
        self.texts = self._load_texts()
    
    def _load_texts(self) -> Dict[str, Dict[str, str]]:
        """Load localized texts."""
        return {
            "en": {
                "welcome": "🤖 Welcome to ASCL Bot Setup Wizard!\n\nThis bot will help you set up your own AI-powered Telegram client that can:\n• Answer questions with AI\n• Respond in your personal style\n• Auto-respond to messages\n• Set custom preferences\n\nChoose your language:",
                "setup_options": "Great! Now choose how you want to set up your ASCL client:",
                "hosting_options": "Choose your hosting option:",
                "api_key_options": "Choose your OpenAI API key option:",
                "telegram_credentials": "Now I need your Telegram API credentials.\n\n📱 Get them from https://my.telegram.org/apps\n\nPlease send your API ID:",
                "telegram_hash": "Great! Now send your API Hash:",
                "telegram_phone": "Perfect! Now send your phone number (with country code, e.g., +1234567890):",
                "openai_key": "Now I need your OpenAI API key.\n\n🔑 Get it from https://platform.openai.com/api-keys\n\nPlease send your API key:",
                "setup_complete": "🎉 Setup Complete!\n\nYour ASCL client is ready! Here's what happens next:",
                "manual_setup": "📋 Manual Setup Instructions\n\nFollow these steps to set up your ASCL client:",
                "auto_setup": "🚀 Automatic Setup\n\nI'll set up everything for you! This will take a few minutes...",
                "personal_hosting": "💻 Personal Hosting\n\nYou'll run the bot on your own computer/server.",
                "server_hosting": "☁️ Server Hosting\n\nWe'll host your bot on our servers (24/7 uptime).",
                "personal_api": "🔑 Personal API Key\n\nYou'll use your own OpenAI API key.",
                "service_api": "💳 Service API Key\n\nWe'll provide the OpenAI API key (paid service).",
                "full_hosting": "🚀 Full Hosting\n\nWe handle everything - API credentials, hosting, and setup. Just provide your phone number!",
                "github_link": "📁 Download from GitHub:\nhttps://github.com/luareload/ascl-bot",
                "support": "💬 Need help? Contact @uffcey"
            },
            "ru": {
                "welcome": "🤖 Добро пожаловать в мастер настройки ASCL бота!\n\nЭтот бот поможет вам настроить собственного AI-клиента для Telegram, который может:\n• Отвечать на вопросы с помощью ИИ\n• Отвечать в вашем личном стиле\n• Автоматически отвечать на сообщения\n• Устанавливать пользовательские предпочтения\n\nВыберите язык:",
                "setup_options": "Отлично! Теперь выберите, как вы хотите настроить ASCL клиент:",
                "hosting_options": "Выберите вариант хостинга:",
                "api_key_options": "Выберите вариант API ключа OpenAI:",
                "telegram_credentials": "Теперь мне нужны ваши учетные данные Telegram API.\n\n📱 Получите их на https://my.telegram.org/apps\n\nПожалуйста, отправьте ваш API ID:",
                "telegram_hash": "Отлично! Теперь отправьте ваш API Hash:",
                "telegram_phone": "Отлично! Теперь отправьте ваш номер телефона (с кодом страны, например, +1234567890):",
                "openai_key": "Теперь мне нужен ваш API ключ OpenAI.\n\n🔑 Получите его на https://platform.openai.com/api-keys\n\nПожалуйста, отправьте ваш API ключ:",
                "setup_complete": "🎉 Настройка завершена!\n\nВаш ASCL клиент готов! Вот что происходит дальше:",
                "manual_setup": "📋 Инструкции по ручной настройке\n\nВыполните эти шаги для настройки ASCL клиента:",
                "auto_setup": "🚀 Автоматическая настройка\n\nЯ настрою все за вас! Это займет несколько минут...",
                "personal_hosting": "💻 Личный хостинг\n\nВы будете запускать бота на своем компьютере/сервере.",
                "server_hosting": "☁️ Серверный хостинг\n\nМы разместим вашего бота на наших серверах (24/7 работа).",
                "personal_api": "🔑 Личный API ключ\n\nВы будете использовать свой собственный API ключ OpenAI.",
                "service_api": "💳 Сервисный API ключ\n\nМы предоставим API ключ OpenAI (платная услуга).",
                "github_link": "📁 Скачать с GitHub:\nhttps://github.com/luareload/ascl-bot",
                "support": "💬 Нужна помощь? Обратитесь к @uffcey"
            }
        }
    
    def get_text(self, user_id: int, key: str) -> str:
        """Get localized text for user."""
        setup = self.user_setups.get(user_id)
        lang = setup.language if setup else "en"
        return self.texts[lang].get(key, key)
    
    def get_user_setup(self, user_id: int) -> UserSetup:
        """Get or create user setup."""
        if user_id not in self.user_setups:
            self.user_setups[user_id] = UserSetup(user_id=user_id)
        return self.user_setups[user_id]

# Global wizard instance
wizard = SetupWizard()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    user_id = update.effective_user.id
    setup = wizard.get_user_setup(user_id)
    setup.step = "language"

    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        wizard.get_text(user_id, "welcome"),
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler."""
    help_text = """🤖 ASCL Bot Setup Wizard

This bot helps you set up your own AI-powered Telegram client.

Commands:
/start - Begin setup wizard
/help - Show this help message
/about - Learn more about ASCL Bot

Features your bot will have:
• AI question answering
• Personal style responses
• Auto-answering mode
• Custom preferences
• Smart skip logic

Get started with /start!"""

    await update.message.reply_text(help_text)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """About command handler."""
    about_text = """🎭 About ASCL Bot

ASCL Bot creates AI-powered Telegram clients that:

🧠 Learn your writing style
⌨️ Type with realistic delays
🎯 Respond intelligently
🛡️ Keep your data private

Pricing:
• Free: Manual setup + personal hosting
• $9.99/month: 24/7 server hosting
• $14.99/month: Unlimited API usage
• $19.99/month: Complete package

Ready to get started? Send /start

📢 Updates: @luareload
💬 Support: @uffcey"""

    await update.message.reply_text(about_text)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    setup = wizard.get_user_setup(user_id)
    data = query.data
    
    if data.startswith("lang_"):
        # Language selection
        setup.language = data.split("_")[1]
        setup.step = "setup_type"
        
        keyboard = [
            [InlineKeyboardButton("🚀 Auto Setup (Recommended)", callback_data="setup_auto")],
            [InlineKeyboardButton("📋 Manual Setup (GitHub)", callback_data="setup_manual")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            wizard.get_text(user_id, "setup_options"),
            reply_markup=reply_markup
        )
    
    elif data.startswith("setup_"):
        # Setup type selection
        setup.setup_type = data.split("_")[1]
        setup.step = "hosting"
        
        keyboard = [
            [InlineKeyboardButton("💻 Personal Hosting (Free)", callback_data="host_personal")],
            [InlineKeyboardButton("☁️ Server Hosting (24/7)", callback_data="host_server")],
            [InlineKeyboardButton("🚀 Full Hosting (Easiest)", callback_data="host_full")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            wizard.get_text(user_id, "hosting_options"),
            reply_markup=reply_markup
        )
    
    elif data.startswith("host_"):
        # Hosting selection
        setup.hosting_type = data.split("_")[1]

        if setup.hosting_type == "full":
            # Full hosting - skip API key selection, go straight to phone
            setup.api_key_type = "service"  # Full hosting includes API service
            setup.step = "phone_number"
            await query.edit_message_text(
                "📱 Phone Number Required\n\nFor full hosting, we need your phone number to set up your Telegram account.\n\nPlease send your phone number (with country code, e.g., +1234567890):"
            )
        else:
            # Regular hosting - show API key options
            setup.step = "api_key"
            keyboard = [
                [InlineKeyboardButton("🔑 My OpenAI Key (Free)", callback_data="api_personal")],
                [InlineKeyboardButton("💳 Service API Key (Paid)", callback_data="api_service")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                wizard.get_text(user_id, "api_key_options"),
                reply_markup=reply_markup
            )
    
    elif data.startswith("api_"):
        # API key selection
        setup.api_key_type = data.split("_")[1]

        if setup.setup_type == "manual":
            await handle_manual_setup(query, user_id)
        elif setup.hosting_type == "full":
            # Full hosting - go to phone number
            setup.step = "phone_number"
            await query.edit_message_text(
                "📱 Phone Number Required\n\nFor full hosting, we need your phone number to set up your Telegram account.\n\nPlease send your phone number (with country code, e.g., +1234567890):"
            )
        else:
            # Regular setup - get Telegram credentials
            setup.step = "telegram_api_id"
            await query.edit_message_text(wizard.get_text(user_id, "telegram_credentials"))

    elif data.startswith("pay_"):
        # Payment handling
        await handle_payment_callback(query, user_id, data)

    elif data == "cancel_payment":
        # Cancel payment
        await query.edit_message_text("❌ Payment cancelled. You can restart the setup anytime with /start")

    elif data.startswith("status_"):
        # Bot status request
        target_user_id = int(data.split("_")[1])
        if target_user_id == user_id:  # Only allow users to check their own status
            from auth_proxy import auth_proxy
            await auth_proxy.handle_status_request(query, target_user_id)

    elif data.startswith("settings_"):
        # Bot settings request
        target_user_id = int(data.split("_")[1])
        if target_user_id == user_id:
            from auth_proxy import auth_proxy
            await auth_proxy.handle_settings_request(query, target_user_id)

    elif data.startswith(("restart_", "stop_", "delete_")):
        # Bot management actions
        action, target_user_id = data.split("_", 1)
        target_user_id = int(target_user_id)
        if target_user_id == user_id:
            from auth_proxy import auth_proxy
            await auth_proxy.handle_bot_action(query, action, target_user_id)

async def handle_payment_callback(query, user_id: int, data: str) -> None:
    """Handle payment callback."""
    parts = data.split("_")  # pay_service_type_billing
    service_type = parts[1] + "_" + parts[2] if len(parts) > 3 else parts[1]
    billing = parts[-1]

    setup = wizard.get_user_setup(user_id)

    # In a real implementation, you would:
    # 1. Create a payment invoice using Telegram Payments API
    # 2. Handle payment confirmation
    # 3. Provision services after successful payment

    # For demo purposes, we'll simulate payment success
    payment_text = f"💳 Payment Processing\n\n"
    payment_text += f"Service: {service_type.replace('_', ' ').title()}\n"
    payment_text += f"Billing: {billing.title()}\n\n"
    payment_text += f"⏳ Processing your payment...\n"
    payment_text += f"You will receive setup instructions shortly."

    await query.edit_message_text(payment_text)

    # Simulate payment processing
    await asyncio.sleep(2)

    # Send success message
    success_text = f"✅ Payment Successful!\n\n"
    success_text += f"Your {service_type.replace('_', ' ')} service is now active.\n"
    success_text += f"Setup instructions have been sent to your DM.\n\n"
    success_text += f"Support: @ascl_support"

    await query.edit_message_text(success_text)

async def handle_manual_setup(query, user_id: int) -> None:
    """Handle manual setup flow."""
    setup = wizard.get_user_setup(user_id)
    
    manual_text = wizard.get_text(user_id, "manual_setup")
    manual_text += f"\n\n{wizard.get_text(user_id, 'github_link')}"
    manual_text += f"\n\n{wizard.get_text(user_id, 'support')}"
    
    await query.edit_message_text(manual_text)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages during setup."""
    user_id = update.effective_user.id
    setup = wizard.get_user_setup(user_id)
    text = update.message.text

    # Import auth proxy for full hosting
    if setup.hosting_type == "full":
        from auth_proxy import auth_proxy

        # Handle authentication steps for full hosting
        auth_step = auth_proxy.get_pending_auth_step(user_id)

        if setup.step == "phone_number":
            # Start phone authentication
            from host_manager import host_manager
            api_cred = host_manager.api_pool.get_available_credential()

            if api_cred:
                setup.telegram_phone = text
                success = await auth_proxy.start_phone_auth(update, user_id, text, api_cred.api_id, api_cred.api_hash)
                if success:
                    setup.step = "verification_code"
            else:
                await update.message.reply_text("❌ No available API credentials. Please try again later.")

        elif auth_step == "code":
            # Handle verification code
            await auth_proxy.handle_verification_code(update, user_id, text)

        elif auth_step == "password":
            # Handle 2FA password
            await auth_proxy.handle_2fa_password(update, user_id, text)

        return

    # Regular setup flow
    if setup.step == "telegram_api_id":
        setup.telegram_api_id = text
        setup.step = "telegram_api_hash"
        await update.message.reply_text(wizard.get_text(user_id, "telegram_hash"))

    elif setup.step == "telegram_api_hash":
        setup.telegram_api_hash = text
        setup.step = "telegram_phone"
        await update.message.reply_text(wizard.get_text(user_id, "telegram_phone"))

    elif setup.step == "telegram_phone":
        setup.telegram_phone = text

        if setup.api_key_type == "personal":
            setup.step = "openai_key"
            await update.message.reply_text(wizard.get_text(user_id, "openai_key"))
        else:
            await complete_setup(update, user_id)

    elif setup.step == "openai_key":
        setup.openai_api_key = text
        await complete_setup(update, user_id)

async def complete_setup(update: Update, user_id: int) -> None:
    """Complete the setup process."""
    setup = wizard.get_user_setup(user_id)
    setup.completed = True
    setup.step = "completed"

    # Generate configuration
    config = await generate_user_config(setup)

    if setup.hosting_type == "server" or setup.api_key_type == "service":
        # Handle paid services
        await handle_payment_flow(update, user_id, setup)
    else:
        # Free setup - provide download and instructions
        await provide_free_setup(update, user_id, config)

async def generate_user_config(setup: UserSetup) -> Dict[str, Any]:
    """Generate user configuration."""
    config = {
        "telegram": {
            "api_id": setup.telegram_api_id,
            "api_hash": setup.telegram_api_hash,
            "phone": setup.telegram_phone
        },
        "openai": {
            "api_key": setup.openai_api_key if setup.api_key_type == "personal" else "SERVICE_PROVIDED"
        },
        "bot": {
            "language": setup.language,
            "hosting": setup.hosting_type,
            "api_type": setup.api_key_type
        }
    }
    return config

async def handle_payment_flow(update: Update, user_id: int, setup: UserSetup) -> None:
    """Handle payment for paid services."""
    prices = {
        "server_hosting": {"monthly": 9.99, "yearly": 99.99},
        "api_service": {"monthly": 14.99, "yearly": 149.99},
        "both": {"monthly": 19.99, "yearly": 199.99},
        "full_hosting": {"monthly": 24.99, "yearly": 249.99}
    }

    if setup.hosting_type == "full":
        service_type = "full_hosting"
    elif setup.hosting_type == "server" and setup.api_key_type == "service":
        service_type = "both"
    elif setup.hosting_type == "server":
        service_type = "server_hosting"
    else:
        service_type = "api_service"

    keyboard = [
        [InlineKeyboardButton(f"💳 Monthly ${prices[service_type]['monthly']}", callback_data=f"pay_{service_type}_monthly")],
        [InlineKeyboardButton(f"💰 Yearly ${prices[service_type]['yearly']} (Save 17%)", callback_data=f"pay_{service_type}_yearly")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    payment_text = f"💳 Payment Required\n\n"
    if setup.hosting_type == "full":
        payment_text += "🚀 Full Hosting Service:\n"
        payment_text += "• ☁️ 24/7 server hosting\n"
        payment_text += "• 🔑 OpenAI API included\n"
        payment_text += "• 📱 No API credentials needed\n"
        payment_text += "• ⚡ Instant setup\n"
    else:
        if setup.hosting_type == "server":
            payment_text += "☁️ Server Hosting (24/7 uptime)\n"
        if setup.api_key_type == "service":
            payment_text += "🔑 OpenAI API Service (unlimited usage)\n"

    payment_text += f"\nChoose your billing cycle:"

    await update.message.reply_text(payment_text, reply_markup=reply_markup)

async def provide_free_setup(update: Update, user_id: int, config: Dict[str, Any]) -> None:
    """Provide free setup instructions and files."""
    setup = wizard.get_user_setup(user_id)

    # Create .env content
    env_content = f"""# Telegram API Configuration
TELEGRAM_API_ID={config['telegram']['api_id']}
TELEGRAM_API_HASH={config['telegram']['api_hash']}
TELEGRAM_PHONE={config['telegram']['phone']}

# OpenAI Configuration
OPENAI_API_KEY={config['openai']['api_key']}

# Bot Configuration
BOT_COMMAND_PREFIX=.ascl
BOT_ANSWER_PREFIX=.ans
BOT_AUTO_ANSWER_PREFIX=.aans
BOT_MANUAL_ANSWER_PREFIX=.mans
BOT_PREFERENCE_PREFIX=.pref

# Language
LANGUAGE={config['bot']['language']}
"""

    # Send configuration file
    await update.message.reply_document(
        document=env_content.encode(),
        filename=".env",
        caption="📁 Your configuration file"
    )

    # Send setup instructions
    instructions = wizard.get_text(user_id, "setup_complete")
    instructions += f"\n\n📋 Next Steps:\n"
    instructions += f"1. Download the ASCL client from GitHub\n"
    instructions += f"2. Replace the .env file with the one I sent\n"
    instructions += f"3. Run: python setup.py\n"
    instructions += f"4. Run: python main.py\n"
    instructions += f"\n{wizard.get_text(user_id, 'github_link')}"
    instructions += f"\n{wizard.get_text(user_id, 'support')}"

    await update.message.reply_text(instructions)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Start the bot
    logger.info("Starting ASCL Setup Wizard Bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
