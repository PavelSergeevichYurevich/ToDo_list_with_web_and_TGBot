import os
import logging
import aiohttp
import json
from pathlib import Path
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[{asctime}] #{levelname:8} {filename}:{lineno} - {name} - {message}',
    style='{'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv("TOKEN")
BASE_URL = "http://127.0.0.1:8000"

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.client.default import DefaultBotProperties

from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
import redis.asyncio as aioredis

redis_conn = aioredis.from_url("redis://localhost:6379/0")
storage = RedisStorage(redis=redis_conn, key_builder=DefaultKeyBuilder(with_destiny=True))

# Инициализация бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=storage)

# Состояния FSM
class FSMFillForm(StatesGroup):
    fill_username = State()
    fill_password = State()

# Клавиатура главного меню
def get_main_keyboard():
    buttons = [
        [InlineKeyboardButton(text='📝 Регистрация', callback_data='button_reg_pressed')],
        [InlineKeyboardButton(text='📊 Все задачи', callback_data='button_show_all')],
        [InlineKeyboardButton(text='⏳ Активные', callback_data='button_show_active')],
        [InlineKeyboardButton(text='✅ Завершенные', callback_data='button_show_closed')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Вспомогательная функция для API запросов
async def call_api(endpoint: str, method: str = 'GET', payload: dict = None):
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == 'GET':
                async with session.get(url) as resp:
                    return await resp.json(), resp.status
            elif method == 'POST':
                async with session.post(url, json=payload) as resp:
                    return await resp.json(), resp.status
        except Exception as e:
            logger.error(f"API Error: {e}")
            return None, 500

# --- ХЕНДЛЕРЫ ---

@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    await message.answer(
        text=f'Привет, {message.from_user.first_name}! Состояния теперь хранятся в Redis.',
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data.startswith('button_show_'))
async def process_show_tasks(callback: CallbackQuery):
    user_tid = callback.from_user.id
    action = callback.data.replace('button_show_', '')
    
    endpoints = {
        "all": f"/task/show/{user_tid}",
        "active": f"/task/showactive/{user_tid}",
        "closed": f"/task/showclosed/{user_tid}"
    }
    
    data, status = await call_api(endpoints.get(action))
    
    if status == 200 and data:
        msg = f"<b>📋 Ваши задачи ({action}):</b>\n\n"
        for i, task in enumerate(data, 1):
            icon = "✅" if task.get('is_completed') else "⏳"
            msg += f"{i}. {icon} <b>{task['title']}</b>\n"
            if task.get('description'):
                msg += f"   └ <i>{task['description']}</i>\n"
            if task.get('deadline'):
                msg += f"   └ <i>{task['deadline']}</i>\n"
            msg += "\n"
    else:
        msg = "📭 Задач не найдено. Зарегистрируйтесь, если еще не сделали этого."
    
    await callback.message.answer(msg, reply_markup=get_main_keyboard())
    await callback.answer()

# --- РЕГИСТРАЦИЯ ЧЕРЕЗ REDIS ---

@dp.callback_query(F.data == 'button_reg_pressed')
async def process_reg_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer('Введите <b>username</b>:')
    await state.set_state(FSMFillForm.fill_username)
    await callback.answer()

@dp.message(StateFilter(FSMFillForm.fill_username))
async def process_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer('Теперь введите <b>пароль</b>:')
    await state.set_state(FSMFillForm.fill_password)

@dp.message(StateFilter(FSMFillForm.fill_password))
async def process_password(message: Message, state: FSMContext):
    # Данные извлекаются из Redis автоматически через state.get_data()
    user_data = await state.get_data()
    username = user_data['username']
    password = message.text
    telegram_id = message.from_user.id
    
    # Отправляем на бэкенд
    payload = {"username": username, "password": password, "telegram_id": telegram_id}
    res, status_code = await call_api("/user/add_tlg/", method='POST', payload=payload)
    
    if status_code == 200:
        await message.answer(f"✅ Успех! Логин: <code>{username}</code>", reply_markup=get_main_keyboard())
        await state.clear() # Очищаем состояние в Redis
    else:
        await message.answer(f"❌ Ошибка регистрации. Возможно, логин занят.")

@dp.message(Command(commands='cancel'))
async def process_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Действие отменено.', reply_markup=get_main_keyboard())

if __name__ == '__main__':
    print("Бот (Redis) запущен...")
    dp.run_polling(bot)
