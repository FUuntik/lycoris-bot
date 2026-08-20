import os
from flask import Flask, request
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Храним состояние пользователей (для простоты, в памяти)
user_states = {}

@app.route('/')
def healthcheck():
    return 'OK', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎨 Дизайнер", callback_data="designer"))
    markup.add(telebot.types.InlineKeyboardButton("💻 Программист", callback_data="programmer"))
    markup.add(telebot.types.InlineKeyboardButton("📢 Пиар-менеджер", callback_data="pr"))
    markup.add(telebot.types.InlineKeyboardButton("📝 Сценарист", callback_data="writer"))
    
    bot.send_message(message.chat.id, "👋 Привет! Кем ты видишь себя в команде?", reply_markup=markup)
    user_states[message.chat.id] = {"state": "role"}

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_states or user_states[chat_id]["state"] != "role":
        bot.answer_callback_query(call.id)
        return
    
    roles = {
        "designer": "🎨 Дизайнер",
        "programmer": "💻 Программист",
        "pr": "📢 Пиар-менеджер",
        "writer": "📝 Сценарист"
    }
    
    role = roles.get(call.data)
    if not role:
        bot.answer_callback_query(call.id)
        return
    
    user_states[chat_id] = {"state": "form", "role": role}
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"✅ Ты выбрал: {role}\n\n"
        "Заполни форму:\n"
        "1. Имя и фамилия\n"
        "2. Возраст\n"
        "3. Опыт\n"
        "4. Контакт\n"
        "5. Почему мы?\n\n"
        "Отправь всё одним сообщением.",
        chat_id=chat_id,
        message_id=call.message.message_id
    )

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == "form")
def handle_form(message):
    chat_id = message.chat.id
    data = user_states[chat_id]
    role = data["role"]
    text = message.text
    user = message.from_user
    
    admin_text = (
        f"📩 Новая заявка!\n\n"
        f"👤 Роль: {role}\n"
        f"📝 Данные:\n{text}\n\n"
        f"От: {user.full_name} (@{user.username or 'нет'})"
    )
    
    bot.send_message(ADMIN_ID, admin_text)
    bot.send_message(chat_id, "✅ Заявка отправлена! Мы с тобой свяжемся.")
    del user_states[chat_id]

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8080))
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    
    app.run(host='0.0.0.0', port=PORT)
