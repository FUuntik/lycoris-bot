import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

ROLE, APPLICATION = range(2)

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎨 Дизайнер", callback_data="designer")],
        [InlineKeyboardButton("💻 Программист", callback_data="programmer")],
        [InlineKeyboardButton("📢 Пиар-менеджер", callback_data="pr")],
        [InlineKeyboardButton("📝 Сценарист", callback_data="writer")]
    ]
    await update.message.reply_text("👋 Привет! Кем ты видишь себя в команде?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ROLE

async def role_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    roles = {
        "designer": "🎨 Дизайнер",
        "programmer": "💻 Программист",
        "pr": "📢 Пиар-менеджер",
        "writer": "📝 Сценарист"
    }
    
    role = roles.get(query.data)
    if not role:
        return ROLE
    
    context.user_data["role"] = role
    await query.edit_message_text(
        f"✅ Ты выбрал: {role}\n\n"
        "Заполни форму:\n"
        "1. Имя и фамилия\n"
        "2. Возраст\n"
        "3. Опыт\n"
        "4. Контакт\n"
        "5. Почему мы?\n\n"
        "Отправь всё одним сообщением."
    )
    return APPLICATION

async def application_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = context.user_data.get("role")
    text = update.message.text
    user = update.message.from_user
    
    admin_text = (
        f"📩 Новая заявка!\n\n"
        f"👤 Роль: {role}\n"
        f"📝 Данные:\n{text}\n\n"
        f"От: {user.full_name} (@{user.username or 'нет'})"
    )
    
    await context.bot.send_message(ADMIN_ID, admin_text)
    await update.message.reply_text("✅ Заявка отправлена! Мы с тобой свяжемся.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ROLE: [CallbackQueryHandler(role_selected)],
            APPLICATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, application_received)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    application.add_handler(conv_handler)
    
    PORT = int(os.environ.get("PORT", 8080))
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    
    await application.initialize()
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )
    await application.start()
    
    # Держим сервер запущенным
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
