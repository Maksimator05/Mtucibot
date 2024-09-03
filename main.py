import telebot
from telebot import types
import sqlite3
import random
import asyncio
import aiosqlite
import copy

bot = telebot.TeleBot('7292212331:AAHc8HtqomP8vidGw1o_9qcM6qJ860GDcMY')
name = None

@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mean TEXT, chat_id TEXT, target_id TEXT)')

    cur.execute(
        'CREATE TABLE IF NOT EXISTS selected_users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mean TEXT, chat_id TEXT, target_id TEXT)')

    conn.commit()
    cur.close()
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Object = types.KeyboardButton('Моя цель')
    Rulls = types.KeyboardButton('Правила')
    markup.row(Object, Rulls)
    Bin = types.KeyboardButton('Очистить душу')
    List = types.KeyboardButton('Список')
    markup.row(Bin, List)


    chat_id = f'{message.from_user.id}'

    # Используем asyncio для запуска асинхронной проверки
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Проверка, существует ли пользователь
    if loop.run_until_complete(user_exists(chat_id)):
        bot.reply_to(message, "Вы уже зарегистрированы!")
    else:
        bot.send_message(message.chat.id,
                         f'Приветствую, {message.from_user.first_name}!\nТы попал на игру "Ловец душ" от МТУСИ\nDesigned by maksimator & tunknowng ',
                         reply_markup=markup)
        bot.send_message(message.chat.id, 'Давай тебя зарегаем. Напиши свое ФИО')
        bot.register_next_step_handler(message, username)


# Функция для получения имени пользователя и его регистрации
def username(message):
    name = message.text  # Имя пользователя, которое он отправил

    # Сохраняем имя пользователя и переходим к запросу хобби
    message.text = name
    bot.reply_to(message, "Отлично! И мне нужно еще твое напрваление")
    bot.register_next_step_handler(message, user_mean, name)


# Функция для получения хобби пользователя и его регистрации
def user_mean(message, name):
    chat_id = message.from_user.id
    mean = message.text  # Хобби, которое пользователь отправил

    # Используем asyncio для регистрации пользователя
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(register_user(name, mean, chat_id))
    bot.reply_to(message, f"Ты зареган\nТвое кодовое слово: {message.from_user.id}")



# Асинхронная функция для регистрации пользователя
async def register_user(name: str, mean: str, chat_id: str):
    async with aiosqlite.connect('Killer.sql') as db:
        await db.execute(
            "INSERT INTO users (name, mean, chat_id) VALUES (?, ?, ?)",
            (name, mean, chat_id)
        )
        await db.commit()

# Асинхронная функция для проверки существования пользователя
async def user_exists(chat_id: str):
    async with aiosqlite.connect('Killer.sql') as db:
        async with db.execute("SELECT 1 FROM users WHERE chat_id = ?", (chat_id,)) as cursor:
            exists = await cursor.fetchone()
            if exists is None:
                async with aiosqlite.connect('Killer.sql') as db:
                    async with db.execute("SELECT 1 FROM selected_users WHERE chat_id = ?", (chat_id,)) as cursor:
                        exists1 = await cursor.fetchone()
                        return exists1 is not None




@bot.message_handler(content_types=['text'])
def send(message):
    if message.text == 'Моя цель':
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        exists = cur.execute("SELECT * FROM users WHERE chat_id = ?", (message.from_user.id,)).fetchone()
        cur.close()
        conn.close()
        if exists:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()

            # Проверяем, есть ли у текущего пользователя уже закрепленный пользователь
            cur.execute("SELECT target_id FROM users WHERE chat_id = ?", (message.from_user.id,))
            target_id_row = cur.fetchone()
            cur.close()
            conn.close()
            if target_id_row[0]:
                bot.send_message(message.chat.id, 'Победа близка')
                conn = sqlite3.connect('Killer.sql')
                cur = conn.cursor()
                cur.execute("SELECT name, mean FROM selected_users WHERE chat_id = ?", (target_id_row[0],))
                assigned_user = cur.fetchone()
                name, mean = assigned_user
                cur.close()
                conn.close()
                bot.send_message(message.chat.id, f"У вас уже закреплен пользователь: {name}, направление: {mean}")
            else:
                select_users(message)
        else:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()

            # Проверяем, есть ли у текущего пользователя уже закрепленный пользователь
            cur.execute("SELECT target_id FROM selected_users WHERE chat_id = ?", (message.from_user.id,))
            target_id_row = copy.deepcopy(cur.fetchone())
            cur.close()
            conn.close()
            if target_id_row[0]:
                bot.send_message(message.chat.id, 'лох не тот, кто лох, а тот, кто экономист')
                conn = sqlite3.connect('Killer.sql')
                cur = conn.cursor()
                cur.execute("SELECT name, mean FROM selected_users WHERE chat_id = ?", (target_id_row[0],))
                assigned_user = cur.fetchone()
                name, mean = assigned_user
                cur.close()
                conn.close()
                bot.send_message(message.chat.id, f"У вас уже закреплен пользователь: {name}, направление: {mean}")
            else:
                select_users(message)

    elif message.text == 'Правила':
        bot.send_message(message.chat.id, 'Правила:')
    elif message.text == 'Очистить душу':
        bot.send_message(message.chat.id, 'Введите кодовое слово')
        bot.register_next_step_handler(message, move_to_bin)
    elif message.text == 'Список':
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users')
        users = cur.fetchall()
        info = 'Чистые души\n'
        for el in users:
            info += f'Имя: {el[1]}, Направление: {el[2]},  {el[4]}\n'

        cur.execute('SELECT * FROM selected_users')
        users = cur.fetchall()
        info += '\nСвязаные души\n'
        for el1 in users:
            info += f'Имя: {el1[1]}, Направление: {el1[2]}, {el1[4]}\n'
        cur.close()
        conn.close()

        bot.send_message(message.chat.id, info)


def move_to_bin(message):
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    cur.execute('DELETE FROM selected_users WHERE chat_id = ?', (message.text.strip(),))
    conn.commit()
    cur.close()
    conn.close()


def select_users(message):
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE NOT chat_id = ?', (message.from_user.id,))
    users = cur.fetchall()
    cur.close()
    conn.close()

    if len(users) > 0:
        info = [[0 for j in range(4)] for i in range(len(users))]
        line = 0
        for el1 in users:
            info[line][0] = f'{el1[1]}'
            info[line][1] = f'{el1[2]}'
            info[line][2] = f'{el1[3]}'
            info[line][3] = f'{el1[4]}'
            line += 1

        selected_user = copy.deepcopy(random.choice(info))
        bot.send_message(message.chat.id, f'Имя: {selected_user[0]}\nНаправление: {selected_user[1]}')
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute("INSERT INTO selected_users (name, mean, chat_id, target_id) SELECT name, mean, chat_id, target_id FROM users" )
        conn.commit()
        chat_id = selected_user[2]
        exists = cur.execute("SELECT 1 FROM users WHERE chat_id = ?", [message.from_user.id]).fetchone()
        cur.close()
        conn.close()
        if exists:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()

            cur.execute("UPDATE users SET target_id = ? WHERE chat_id = ?", (chat_id, message.from_user.id,))

            conn.commit()
            cur.close()
            conn.close()
        else:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()

            cur.execute("UPDATE selected_users SET target_id = ? WHERE chat_id = ?", (chat_id, message.from_user.id,))

            conn.commit()
            cur.close()
            conn.close()
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE chat_id = ?', (selected_user[2],))
        conn.commit()
        cur.close()
        conn.close()
    else:
        bot.send_message(message.chat.id, 'Никого нет дома')


bot.polling(none_stop=True)
