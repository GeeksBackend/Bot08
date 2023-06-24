from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from email.message import EmailMessage
import os, logging, smtplib

load_dotenv('.env')

bot = Bot(os.environ.get('token'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

inline_keyboards = [
    InlineKeyboardButton('Отправить сообщение', callback_data='send_button'),
    InlineKeyboardButton('Наш сайт', url='https://geeks.kg')
]
inline_button = InlineKeyboardMarkup().add(*inline_keyboards)

@dp.message_handler(commands='start')
async def start(message:types.Message):
    await message.answer('Привет! Я помогу тебе отправить сообщение на почту\nНапиши /send', reply_markup=inline_button)

@dp.callback_query_handler(lambda call: call)
async def all_inline(call):
    if call.data == 'send_button':
        await send_command(call.message)

#to_email, subject, message
class EmailState(StatesGroup):
    to_email = State()
    subject = State()
    message = State()

@dp.message_handler(commands='send')
async def send_command(message:types.Message):
    await message.answer('Введите почту на которую нужно отправить сообщение')
    await EmailState.to_email.set()

@dp.message_handler(state=EmailState.to_email)
async def get_subject(message:types.Message, state:FSMContext):
    await state.update_data(to_email=message.text)
    await message.answer('Введите заголовок')
    await EmailState.subject.set()

@dp.message_handler(state=EmailState.subject)
async def get_message(message:types.Message, state:FSMContext):
    await state.update_data(subject=message.text)
    await message.answer('Введите сообщение')
    await EmailState.message.set()

@dp.message_handler(state=EmailState.message)
async def send_message(message:types.Message, state:FSMContext):
    await state.update_data(message=message.text)
    await message.answer('Отправляем почту...')
    res = await storage.get_data(user=message.from_user.id)
    sender = os.environ.get('smtp_email')
    password = os.environ.get('smtp_email_password')

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    msg = EmailMessage()
    msg.set_content(res['message'])

    msg['Subject'] = res['subject']
    msg['From'] = os.environ.get('smtp_email')
    msg['To'] = res['to_email']

    try:
        server.login(sender, password)
        server.send_message(msg)
        await message.answer('Успешно отправлено!')
    except Exception as error:
        await message.answer(f'Произошла ошибка попробуйте позже\n{error}')
    await state.finish()

executor.start_polling(dp)