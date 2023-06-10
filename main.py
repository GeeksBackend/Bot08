from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from config import token
import sqlite3, time, logging

bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

database = sqlite3.connect('users.db')
cursor = database.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INT,
    chat_id INT,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created VARCHAR(100)
);
""")
cursor.connection.commit()

keyboard_buttons = [
    KeyboardButton('/start'),
    KeyboardButton('/help'),
    KeyboardButton('/test'),
    KeyboardButton('/mailing')
]
keyboard_one = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=30).add(*keyboard_buttons)

@dp.message_handler(commands='start')
async def start(message:types.Message):
    cursor.execute(f"SELECT * FROM users WHERE user_id = {message.from_user.id};")
    result = cursor.fetchall()
    if result == []:
        cursor.execute(f"""INSERT INTO users VALUES ({message.from_user.id},
                    {message.chat.id}, '{message.from_user.username}',
                    '{message.from_user.first_name}', 
                    '{message.from_user.last_name}',
                    '{time.ctime()}');
                    """)
    cursor.connection.commit()
    await message.answer(f"Привет {message.from_user.full_name}!", reply_markup=keyboard_one)

@dp.message_handler(commands='help')
async def help(message:types.Message):
    await message.answer("Чем я могу вам помочь?")

@dp.message_handler(text="Привет")
async def hello(message:types.Message):
    await message.reply("Приветик")

@dp.message_handler(commands='test')
async def testing(message:types.Message):
    await message.answer_dice()
    await message.answer_location(40.51933912658552, 72.80307604619333)
    await message.answer_photo("https://lh4.googleusercontent.com/n6Qbp6DJX0Kv8nl4Se7_FDoZlXyIXdBWYV7SaA-FCw-ZkR2uGrAqb1ssxft2SbRA4yrgk8-IVhd3vFkzoWma6o9Jc0HrUSffhNC8-Z0PuVDPF30up-CvppiczhNMw0Iro_XUzTqu9JrMRAhmU0oTOrc")

class MailingState(StatesGroup):
    text = State()

@dp.message_handler(commands='mailing')
async def mailing(message:types.Message):
    if message.from_user.id in [731982105]:
        await message.reply("Введите текст для рассылки:")
        await MailingState.text.set()
    else:
        await message.answer("У вас нет прав")

@dp.message_handler(state=MailingState.text)
async def send_mailing_text(message:types.Message, state:FSMContext):
    await message.answer("Начинаю рассылку...")
    cursor.execute("SELECT chat_id FROM users;")
    chats_id = cursor.fetchall()
    for chat in chats_id:
        await bot.send_message(chat[0], message.text)
    await message.answer("Рассылка окончена!")
    await state.finish()

@dp.message_handler()
async def not_found(message:types.Message):
    await message.reply("Я вас не понял, введите /help")

executor.start_polling(dp)