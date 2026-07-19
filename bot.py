import logging
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# ─── Configuration ────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "8995091020:AAHqkFsCAJb5GXsWvRtRIsEiiNuoFjVF0Bc"
CLAUDE_API_KEY     = "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"
CLAUDE_MODEL       = "claude-haiku-4-5"

# ─── Proxy Settings (optional) ────────────────────────────────────────────────
# If Telegram is blocked in your country, set a proxy below.
# Examples:
#   HTTP  proxy: "http://127.0.0.1:8080"
#   SOCKS5 proxy: "socks5://127.0.0.1:1080"
# Leave as None to connect directly.
PROXY_URL = None  # e.g. "socks5://127.0.0.1:1080"

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Anthropic Client ─────────────────────────────────────────────────────────
claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# Store conversation history per user
conversation_history: dict[int, list] = {}

# ─── Handlers ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message when user types /start"""
    user = update.effective_user
    welcome = (
        f"✨ Hello {user.first_name}! I'm **Genie** 🧞‍♂️\n\n"
        "I'm powered by Claude AI and ready to help you with anything!\n\n"
        "Just type your message and I'll respond instantly.\n\n"
        "Commands:\n"
        "• /start — Show this welcome message\n"
        "• /clear — Clear conversation history\n"
        "• /help  — Show help info"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")
    logger.info(f"User {user.id} ({user.first_name}) started the bot.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help info"""
    help_text = (
        "🧞‍♂️ *Genie Bot Help*\n\n"
        "I'm an AI assistant powered by Claude (Anthropic).\n\n"
        "*What I can do:*\n"
        "• Answer any question\n"
        "• Write code & debug\n"
        "• Summarize text\n"
        "• Have full conversations (I remember context!)\n\n"
        "*Commands:*\n"
        "• /start — Restart the bot\n"
        "• /clear — Clear our conversation history\n"
        "• /help  — Show this message"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear conversation history for this user"""
    user_id = update.effective_user.id
    conversation_history.pop(user_id, None)
    await update.message.reply_text("🗑️ Conversation history cleared! Starting fresh.")
    logger.info(f"Cleared history for user {user_id}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages and respond with Claude AI"""
    user     = update.effective_user
    user_id  = user.id
    user_msg = update.message.text

    logger.info(f"Message from {user.first_name} ({user_id}): {user_msg}")

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Build/update conversation history
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_msg
    })

    # Keep last 20 messages to avoid token limits
    history = conversation_history[user_id][-20:]

    try:
        response = claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=(
                "You are Genie 🧞‍♂️, a friendly and intelligent AI assistant "
                "living inside a Telegram bot. Be helpful, concise, and conversational. "
                "Use emojis occasionally to make responses feel warm and engaging."
            ),
            messages=history
        )

        ai_reply = response.content[0].text

        # Save assistant reply to history
        conversation_history[user_id].append({
            "role": "assistant",
            "content": ai_reply
        })

        await update.message.reply_text(ai_reply)
        logger.info(f"Replied to {user.first_name}: {ai_reply[:80]}...")

    except anthropic.AuthenticationError:
        await update.message.reply_text("❌ Claude API key is invalid. Please check the configuration.")
        logger.error("Authentication error with Claude API.")

    except anthropic.RateLimitError:
        await update.message.reply_text("⚠️ Rate limit hit. Please wait a moment and try again.")
        logger.warning("Rate limit error from Claude API.")

    except Exception as e:
        await update.message.reply_text(f"❌ Something went wrong: {str(e)}")
        logger.error(f"Error: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    logger.info("🚀 Starting Genie Bot...")

    # Build app with optional proxy support
    builder = Application.builder().token(TELEGRAM_BOT_TOKEN)

    if PROXY_URL:
        logger.info(f"🔒 Using proxy: {PROXY_URL}")
        request = HTTPXRequest(proxy=PROXY_URL)
        builder = builder.request(request)
    else:
        logger.info("🌐 Connecting directly (no proxy)")

    app = builder.build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_command))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Genie Bot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
