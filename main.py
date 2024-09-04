import telebot
from telebot import types
import sqlite3
import random
import asyncio
import aiosqlite
import copy

bot = telebot.TeleBot('7292212331:AAHc8HtqomP8vidGw1o_9qcM6qJ860GDcMY')


@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mean TEXT, chat_id TEXT, target_id TEXT)')

    cur.execute('CREATE TABLE IF NOT EXISTS selected_users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mean TEXT, chat_id TEXT, target_id TEXT)')
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

    chat_id = f'{message.chat.id}'

    # Используем asyncio для запуска асинхронной проверки
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Проверка, существует ли пользователь
    if loop.run_until_complete(user_exists(chat_id)):
        bot.send_message(message.chat.id, "Вы уже зарегистрированы!")
    else:
        bot.send_message(message.chat.id,
                         f'Приветствую, {message.from_user.first_name}!\nТы попал на игру "Собиратель душ" от МТУСИ\nDesigned by maksimator & tunknowng', reply_markup=markup)
        bot.send_message(message.chat.id, 'Давай тебя зарегаем. Напиши свое ФИО')
        bot.register_next_step_handler(message, get_username)


# Функция для получения имени пользователя и его регистрации
def get_username(message):
    name = message.text  # Имя пользователя, которое он отправил
    bot.send_message(message.chat.id, "Отлично! И мне нужно еще твое направление")
    bot.register_next_step_handler(message, get_user_mean, name)


# Функция для получения направления пользователя и его регистрации
def get_user_mean(message, name):
    mean = message.text
    chat_id = message.chat.id

    # Используем asyncio для регистрации пользователя
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(register_user(name, mean, chat_id))
    bot.send_message(message.chat.id, f"Ты зареган\nТвое кодовое слово: {chat_id}")


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
        async with db.execute("SELECT 1 FROM users WHERE chat_id = ?",
                              (chat_id,)) as cursor:
            exists = await cursor.fetchone()
            find = exists is not None
            if find:
                return find
            else:
                async with aiosqlite.connect('Killer.sql') as db:
                    async with db.execute("SELECT 1 FROM selected_users WHERE chat_id = ?",
                                          (chat_id,)) as cursor:
                        exists1 = await cursor.fetchone()
                        return exists1 is not None



@bot.message_handler(content_types=['text'])
def send(message):
    if message.text == 'Моя цель':
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        exists = cur.execute("SELECT * FROM users WHERE chat_id = ?",
                             (message.chat.id,)).fetchone()
        cur.close()
        conn.close()

        if exists:
            # Проверяем, есть ли у текущего пользователя уже закрепленный пользователь
            if exists[4]:
                conn = sqlite3.connect('Killer.sql')
                cur = conn.cursor()
                assigned_user = cur.execute("SELECT * FROM selected_users WHERE chat_id = ?",
                                            (exists[4],)).fetchone()
                cur.close()
                conn.close()

                if assigned_user:
                    bot.send_message(message.chat.id, f"У вас уже закреплен пользователь: {assigned_user[1]}, направление: {assigned_user[2]}")
                else:
                    bot.send_message(message.chat.id, f"У вас уже был закреплен пользователь, но его душа неожиданно пропала")

                    conn = sqlite3.connect('Killer.sql')
                    cur = conn.cursor()
                    cur.execute("UPDATE users SET target_id = ? WHERE chat_id = ?",
                                (None, message.chat.id,))
                    conn.commit()
                    cur.close()
                    conn.close()
            else:
                select_users(message)
        else:
            # Проверяем, есть ли у текущего пользователя уже закрепленный пользователь
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()
            user = cur.execute("SELECT * FROM selected_users WHERE chat_id = ?",
                               (message.chat.id,)).fetchone()
            cur.close()
            conn.close()

            if user and user[4]:
                conn = sqlite3.connect('Killer.sql')
                cur = conn.cursor()
                assigned_user = cur.execute("SELECT * FROM selected_users WHERE chat_id = ?",
                                            (user[4],)).fetchone()
                cur.close()
                conn.close()

                if assigned_user:
                    bot.send_message(message.chat.id, f"У вас уже закреплен пользователь: {assigned_user[1]}, направление: {assigned_user[2]}")
                else:
                    bot.send_message(message.chat.id, f"У вас уже был закреплен пользователь, но его душа неожиданно пропала")

                    conn = sqlite3.connect('Killer.sql')
                    cur = conn.cursor()
                    cur.execute("UPDATE selected_users SET target_id = ? WHERE chat_id = ?",
                                (None, message.chat.id,))
                    conn.commit()
                    cur.close()
                    conn.close()
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

    exists = (cur.execute("SELECT * FROM selected_users ").fetchall())
    if len(exists) == 2:
        bot.send_message(message.chat.id, 'Вы победитель. Поздравляю!!!')

    cur.close()
    conn.close()
    bot.send_message(message.text.strip(), 'Вас очистили. Вы проиграли')
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    cur.execute('DELETE FROM selected_users WHERE chat_id = ?',
                (message.text.strip(),))
    conn.commit()
    cur.close()
    conn.close()


def select_users(message):
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    users = cur.execute('SELECT * FROM users WHERE NOT chat_id = ?',
                        (message.from_user.id,)).fetchall()
    cur.close()
    conn.close()

    if len(users) > 0:
        info = [[0 for j in range(4)] for i in range(len(users))]
        line = 0
        for el1 in users:
            info[line][0] = el1[1]
            info[line][1] = el1[2]
            info[line][2] = el1[3]
            info[line][3] = el1[4]
            line += 1

        selected_user = copy.deepcopy(random.choice(info))
        bot.send_message(message.chat.id, f'Имя: {selected_user[0]}\nНаправление: {selected_user[1]}')

        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute("INSERT INTO selected_users (name, mean, chat_id, target_id) VALUES (?, ?, ?, ?)",
                    (selected_user[0], selected_user[1], selected_user[2], selected_user[3],))
        conn.commit()
        exists = cur.execute("SELECT * FROM users WHERE chat_id = ?",
                             (message.chat.id,)).fetchone()
        cur.close()
        conn.close()

        if exists:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()
            cur.execute("UPDATE users SET target_id = ? WHERE chat_id = ?",
                        (selected_user[2], message.chat.id,))
            conn.commit()
            cur.close()
            conn.close()
        else:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()
            cur.execute("UPDATE selected_users SET target_id = ? WHERE chat_id = ?",
                        (selected_user[2], message.chat.id,))
            conn.commit()
            cur.close()
            conn.close()

        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE chat_id = ?',
                    (selected_user[2],))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        selected_users = cur.execute('SELECT * FROM selected_users WHERE NOT chat_id = ?',
                            (message.from_user.id,)).fetchall()
        cur.close()
        conn.close()
        if len(selected_users) > 0:
            info = [[0 for j in range(4)] for i in range(len(selected_users))]
            line = 0
            for el1 in selected_users:
                info[line][0] = el1[1]
                info[line][1] = el1[2]
                info[line][2] = el1[3]
                info[line][3] = el1[4]
                line += 1

            selected_user = copy.deepcopy(random.choice(info))
            bot.send_message(message.chat.id, f'Имя: {selected_user[0]}\nНаправление: {selected_user[1]}')

            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()
            exists = cur.execute("SELECT * FROM users WHERE chat_id = ?",
                                 (message.chat.id,)).fetchone()
            cur.close()
            conn.close()

            if exists:
                conn = sqlite3.connect('Killer.sql')
                cur = conn.cursor()
                cur.execute("UPDATE users SET target_id = ? WHERE chat_id = ?",
                            (selected_user[2], message.chat.id,))
                conn.commit()
                cur.close()
                conn.close()
            else:
                conn = sqlite3.connect('Killer.sql')
                cur = conn.cursor()
                cur.execute("UPDATE selected_users SET target_id = ? WHERE chat_id = ?",
                            (selected_user[2], message.chat.id,))
                conn.commit()
                cur.close()
                conn.close()
        else:
            bot.send_message(message.chat.id, 'Никого нет дома')


bot.polling(none_stop=True)
