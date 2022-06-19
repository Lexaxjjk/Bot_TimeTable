from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message
import logging
import sqlite3
from parse_data import table
import datetime
from datetime import datetime

API_TOKEN = '5470515481:AAG0XMSEkwf8T9rScCsJMiGlILyqfqrkLcI'
ADMIN = 457235837

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect('db.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(user_id INTEGER, user_firstname INTEGER, user_lastname INTEGER);')
conn.commit()


class dialog(StatesGroup):
    spam = State()
    in_user_date = State()
    set_user_date = State()


stations_index = {'Борщагівка': '83', 'Святошин': '85', 'Новобіличі': '86', 'Біличі': '87', 'Ірпінь': '88',
                  'Лісова Буча': '89', 'Буча': '90', 'Склозаводська': '91', 'Ворзель': '92', 'Кічеєве': '93',
                  'Немішаєве': '94', 'Клавдієво-Тарасове': '95', 'Макійчукове': '96', 'Бородянка': '97',
                  'Хутір Гай': '98', 'Загальці': '99', 'Спартак': '100', 'Піски': '101', 'Тетерів': '102'}

stations = []

current_date = str(datetime.now().date())

kb_admin_home = types.ReplyKeyboardMarkup(resize_keyboard=True)
user_date = current_date

kb_home_user = types.ReplyKeyboardMarkup(resize_keyboard=True)
kb_home_user.add(types.InlineKeyboardButton(text='Розклад на сьогодні'))
kb_home_user.add(types.InlineKeyboardButton(text='Розклад на вказану дату'))

kb_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
kb_back.add(types.InlineKeyboardButton(text='Назад'))

keyboard_stations = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_stations.add(*stations_index.keys())


def check_format_date(date):
    format_date = '%Y-%m-%d'
    try:
        result = bool(datetime.strptime(date, format_date))
    except ValueError:
        result = False
    return result


def set_button_for_admin():
    if len(kb_admin_home['keyboard']) == 0:
        kb_admin_home.add(types.InlineKeyboardButton(text='Рассылка'))
        kb_admin_home.add(types.InlineKeyboardButton(text='Статистика'))
        kb_admin_home.add(types.InlineKeyboardButton(text='Розклад на сьогодні'))
        kb_admin_home.add(types.InlineKeyboardButton(text='Розклад на вказану дату'))


@dp.message_handler(commands=['start'])
async def start(message: Message):
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM users WHERE user_id = {message.chat.id}')
    result = cursor.fetchone()
    if message.from_user.id == ADMIN:
        set_button_for_admin()
        await message.answer('Добро пожаловать в Админ-Панель! Выберите действие на клавиатуре',
                             reply_markup=kb_admin_home)
        return
    if result is None:
        cursor.execute(
            f"INSERT INTO users VALUES ("
            f"'{message.from_user.id}', '{message.from_user.first_name}', '{message.from_user.last_name}')")
        conn.commit()
    await message.answer(f'Привіт {message.from_user.first_name}\n'
                         f'Оберіть дату:', reply_markup=kb_home_user)


@dp.message_handler(content_types=['text'], text='Розклад на вказану дату')
async def start_time_table_in_user_date(message: Message):
    await dialog.set_user_date.set()
    await message.answer('Напишіть дату в форматі "РРРР-ММ-ДД" (Приклад: 2022-02-22)', reply_markup=kb_back)


@dp.message_handler(state=dialog.set_user_date)
async def time_table_in_user_date(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await message.answer('Головне меню', reply_markup=kb_home_user)
        await state.finish()
    elif check_format_date(message.text):
        global user_date
        user_date = message.text
        await dialog.in_user_date.set()
        await message.answer(f'Оберіть станцію відправлення:', reply_markup=keyboard_stations)
    else:
        await message.answer(f'Дата введена не вірно!!!\nСпробуйте ще раз!')


@dp.message_handler(content_types=['text'], text='Розклад на сьогодні')
async def start_time_table_in_current_date(message: Message):
    await dialog.in_user_date.set()
    await message.answer(f'Оберіть станцію відправлення:', reply_markup=keyboard_stations)


@dp.message_handler(state=dialog.in_user_date)
async def time_table_in_current_date(message: types.Message, state: FSMContext):
    if not (message.text in stations_index.keys()):
        await message.answer(f'Станцію не знайдено!')
        return

    if len(stations) == 0:
        stations.append(message.text)
        await message.answer(f'Ви обрали {stations[0]}\n'
                             f'Оберіть станцію призначення:')

    elif len(stations) == 1:
        stations.append(message.text)
        await message.answer(f'Ви обрали {stations[1]}\n'
                             f'Дякую. За мить ви отримаєте актуальний розклад на сьогодні!')
        table(stations_index[stations[0]], stations_index[stations[1]], stations[0], stations[1], user_date)
        stations.clear()
        photo = open('tableData.png', 'rb')
        await bot.send_photo(chat_id=message.chat.id, photo=photo)
        if message.from_user.id == ADMIN:
            set_button_for_admin()
            await message.answer('Вы возвращены в Админ-Панель! Выберите действие на клавиатуре',
                                 reply_markup=kb_admin_home)
        else:
            await message.answer(f'Дякуємо що користуєтесь <b>@RozkladRuhu_kiev_bot</b>\n'
                                 f'Вас повернено до головної сторінки.', parse_mode='html',
                                 reply_markup=kb_home_user)
        await state.finish()


@dp.message_handler(content_types=['text'], text='Рассылка')
async def spam(message: Message):
    if message.chat.id == ADMIN:
        await dialog.spam.set()
        await message.answer('Напиши текст рассылки', reply_markup=kb_back)


@dp.message_handler(state=dialog.spam)
async def start_spam(message: Message, state: FSMContext):
    if message.text == 'Назад':
        set_button_for_admin()
        await message.answer('Главное меню', reply_markup=kb_admin_home)
        await state.finish()
    else:
        cursor = conn.cursor()
        cursor.execute(f'SELECT user_id FROM users')
        spam_base = cursor.fetchall()
        for user_index in range(len(spam_base)):
            await bot.send_message(spam_base[user_index][0], message.text)
        set_button_for_admin()
        await message.answer('Рассылка завершена', reply_markup=kb_admin_home)
        await state.finish()


@dp.message_handler(content_types=['text'], text='Статистика')
async def statistics(message: types.Message):
    if message.chat.id == ADMIN:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        results = cursor.fetchall()
        await message.answer(f'Людей которые когда либо заходили в бота: {len(results)}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
