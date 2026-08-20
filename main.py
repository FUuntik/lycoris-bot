import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)

class Form(StatesGroup):
    role = State()
    application = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎨 Дизайнер", callback_data="role_designer")],
        [types.InlineKeyboardButton(text="💻 Программист", callback_data="role_programmer")],
        [types.InlineKeyboardButton(text="📢 Пиар-менеджер", callback_data="role_pr")],
        [types.InlineKeyboardButton(text="📝 Сценарист", callback_data="role_writer")]
    ])
    await message.answer("👋 Привет! Кем ты видишь себя в команде?", reply_markup=kb)
    await state.set_state(Form.role)

@dp.callback_query(Form.role)
async def process_role(callback: types.CallbackQuery, state: FSMContext):
    roles = {
        "role_designer": "🎨 Дизайнер",
        "role_programmer": "💻 Программист",
        "role_pr": "📢 Пиар-менеджер",
        "role_writer": "📝 Сценарист"
    }
    role = roles.get(callback.data)
    if not role:
        return
    
    await state.update_data(role=role)
    await callback.answer()
    await callback.message.edit_text(
        f"✅ Ты выбрал: {role}\n\n"
        "Заполни форму:\n"
        "1. Имя и фамилия\n"
        "2. Возраст\n"
        "3. Опыт\n"
        "4. Контакт\n"
        "5. Почему мы?\n\n"
        "Отправь всё одним сообщением."
    )
    await state.set_state(Form.application)

@dp.message(Form.application)
async def process_app(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("role")
    text = message.text
    
    admin_text = (
        f"📩 Новая заявка!\n\n"
        f"👤 Роль: {role}\n"
        f"📝 Данные:\n{text}\n\n"
        f"От: {message.from_user.full_name} (@{message.from_user.username or 'нет'})"
    )
    await bot.send_message(ADMIN_ID, admin_text)
    await message.answer("✅ Заявка отправлена! Мы с тобой свяжемся.")
    await state.clear()

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

def main():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    dp.startup.register(on_startup)
    
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
