from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from pytube import YouTube
import sqlite3, time, logging, os

load_dotenv('.env')

bot = Bot(os.environ.get('token'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

database = sqlite3.connect('youtube.db')
cursor = database.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INT,
    chat_id INT,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(200),
    email VARCHAR(200),
    created VARCHAR(100)
);
""")
cursor.connection.commit()

inline_buttons = [
    InlineKeyboardButton('Скачать аудио', callback_data='audio'),
    InlineKeyboardButton('Скачать видео', callback_data='video'),
    InlineKeyboardButton('Наш сайт', url='https://geeks.edu.kg/'),
    # InlineKeyboardButton('Оплатить', pay=True)
    # InlineKeyboardButton('Окошко', web_app='https://geeks.edu.kg/')
]
inline_keyboard = InlineKeyboardMarkup().add(*inline_buttons)

class FormatState(StatesGroup):
    url = State()
    format_url = State()

class AudioState(StatesGroup):
    url = State()

class VideoState(StatesGroup):
    url = State()

@dp.callback_query_handler(lambda call: call)
async def all_inline(call):
    if call.data == 'audio':
        await bot.send_message(call.message.chat.id, 'Отправьте ссылку на аудио')
        await AudioState.url.set()
    elif call.data == 'video':
        await bot.send_message(call.message.chat.id, 'Отправьте ссылку на видео')
        await VideoState.url.set()

@dp.message_handler(state=AudioState.url)
async def download_audio(message:types.Message, state:FSMContext):
    yt = YouTube(message.text, use_oauth=True)
    await message.answer("Скачиваем аудио, ожидайте...")
    try:
        yt.streams.filter(only_audio=True).first().download('audio', f'{yt.title}.mp3')
        await message.answer("Скачалось, отправляю...")
        with open(f'audio/{yt.title}.mp3', 'rb') as audio:
            await bot.send_audio(message.chat.id, audio, reply_markup=inline_keyboard)
        os.remove(f'audio/{yt.title}.mp3')
    except:
        yt.streams.filter(only_audio=True).first().download('audio', f'{yt.author}.mp3')
        await message.answer("Скачалось, отправляю...")
        with open(f'audio/{yt.author}.mp3', 'rb') as audio:
            await bot.send_audio(message.chat.id, audio, reply_markup=inline_keyboard)
        os.remove(f'audio/{yt.author}.mp3')
    await state.finish()

@dp.message_handler(state=VideoState.url)
async def download_video(message:types.Message, state:FSMContext):
    yt = YouTube(message.text, use_oauth=True)
    await message.answer("Скачиваем видео...")
    try:
        yt.streams.filter(file_extension='mp4').first().download('video', f'{yt.title}.mp4')
        await message.answer("Скачалось, отправляю...")
        with open(f'video/{yt.title}.mp4', 'rb') as video:
            await bot.send_video(message.chat.id, video, reply_markup=inline_keyboard)
        os.remove(f'video/{yt.title}.mp4')
    except:
        yt.streams.filter(file_extension='mp4').first().download('video', f'{yt.author}.mp4')
        await message.answer("Скачалось, отправляю...")
        with open(f'video/{yt.author}.mp4', 'rb') as video:
            await bot.send_video(message.chat.id, video, reply_markup=inline_keyboard)
        os.remove(f'video/{yt.author}.mp4')
    await state.finish()

@dp.message_handler(commands='start')
async def start(message:types.Message):
    cursor.execute(f"SELECT * FROM users WHERE user_id = {message.from_user.id};")
    result = cursor.fetchall()
    if result == []:
        cursor.execute(f"""INSERT INTO users (user_id, chat_id, username, first_name,
                    last_name, created) VALUES ({message.from_user.id},
                    {message.chat.id}, '{message.from_user.username}',
                    '{message.from_user.first_name}', 
                    '{message.from_user.last_name}',
                    '{time.ctime()}');
                    """)
    cursor.connection.commit()
    await message.answer(f"Привет {message.from_user.full_name}!\nЯ помогу тебе скачать видео или же аудио с ютуба. Просто отправь ссылку из ютуба )", reply_markup=inline_keyboard)

verify_buttons = [
    KeyboardButton('Отправить номер', request_contact=True),
    KeyboardButton('Отправить свое местоположение', request_location=True)
]
verify_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*verify_buttons)

@dp.message_handler(commands='verify')
async def verify_user(message:types.Message):
    await message.answer('Для верификации отправьте свой номер телефона', reply_markup=verify_keyboard)

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def get_phone_number(messsage:types.Message):
    await messsage.answer(f"{messsage.contact.phone_number}")
    cursor.execute(f"""UPDATE users SET phone = {messsage.contact.phone_number} 
                   WHERE user_id = {messsage.from_user.id};""")
    cursor.connection.commit()
    await messsage.answer("Ваш номер телефона успешно записан")

format_buttons = [
    KeyboardButton('Mp3'),
    KeyboardButton('Mp4')
]

format_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*format_buttons)

@dp.message_handler()
async def get_youtube_url(message:types.Message, state:FSMContext):
    if 'https://youtu.be/' in message.text:
        await message.reply("В каком формате вы хотите получить результат?", reply_markup=format_keyboard)
        await state.update_data(url=message.text)
        await FormatState.format_url.set()
    else:
        await message.reply("Неправильный формат ссылки")

@dp.message_handler(state=FormatState.format_url)
async def download(message:types.Message, state:FSMContext):
    url = await storage.get_data(user=message.from_user.id)
    yt = YouTube(url['url'], use_oauth=True)
    if message.text == 'Mp3':
        await message.answer("Скачиваем аудио, ожидайте...")
        try:
            yt.streams.filter(only_audio=True).first().download('audio', f'{yt.title}.mp3')
            await message.answer("Скачалось, отправляю...")
            with open(f'audio/{yt.title}.mp3', 'rb') as audio:
                await bot.send_audio(message.chat.id, audio)
            os.remove(f'audio/{yt.title}.mp3')
        except:
            yt.streams.filter(only_audio=True).first().download('audio', f'{yt.author}.mp3')
            await message.answer("Скачалось, отправляю...")
            with open(f'audio/{yt.author}.mp3', 'rb') as audio:
                await bot.send_audio(message.chat.id, audio)
            os.remove(f'audio/{yt.author}.mp3')
    elif message.text == 'Mp4':
        await message.answer("Скачиваем видео...")
        try:
            yt.streams.filter(file_extension='mp4').first().download('video', f'{yt.title}.mp4')
            await message.answer("Скачалось, отправляю...")
            with open(f'video/{yt.title}.mp4', 'rb') as video:
                await bot.send_video(message.chat.id, video)
            os.remove(f'video/{yt.title}.mp4')
        except:
            yt.streams.filter(file_extension='mp4').first().download('video', f'{yt.author}.mp4')
            await message.answer("Скачалось, отправляю...")
            with open(f'video/{yt.author}.mp4', 'rb') as video:
                await bot.send_video(message.chat.id, video)
            os.remove(f'video/{yt.author}.mp4')
    await state.finish()

executor.start_polling(dp)