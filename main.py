import telebot
from telebot import types
import sqlite3
import random
import asyncio
import aiosqlite
import copy
import os
from dotenv import load_dotenv

load_dotenv()
Pass_Word = os.getenv("PASSWORD")
bot_token = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(bot_token)


@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mean TEXT, chat_id TEXT, target_id TEXT)')

    cur.execute('CREATE TABLE IF NOT EXISTS selected_users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mean TEXT, chat_id TEXT, target_id TEXT)')

    cur.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, name TEXT, chat_id TEXT)')
    conn.commit()
    cur.close()
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Object = types.KeyboardButton('Моя цель')
    Rulls = types.KeyboardButton('Правила')
    markup.row(Object, Rulls)
    Bin = types.KeyboardButton('Очистить душу')
    List = types.KeyboardButton('Число онлайна')
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
                         f'Приветствую, {message.from_user.first_name}!\nТы попал на игру "Собиратель душ" от МТУСИ', reply_markup=markup)
        bot.send_message(message.chat.id, 'Правила:\n'
                                          'Вы должны пройти регистрацию написав свое ФИО!!, а так же свое направление(ИТ, РИТ и т.п.).\n'
                                          'Смысл игры заключается в том, чтобы очистить все души и остаться последней душой.\n'
                                          'У вас есть 4 кнопки для управления игрой:\n'
                                          '"Моя цель" - при нажатии выводит вашу действующую цель, которую вы должны найти и очистить.\n'
                                          'Для того, чтобы очистить душу вам следует найти этого человека в реальной жизни и спросить у него его код, '
                                          'который понадобиться для очищения, а также для доказательства нужно будет сфотографироваться с очищенной душой и отправить по ссылке админу (@aokom02) для проверки.\n'
                                          'После чего вам будет доступна новая цель.\n'
                                          'Правила - при нажатии выводит эти самые правила, чтобы еще раз с ними ознакомиться, если вы вдруг забыли.\n'
                                          'Очистить душу - самая главная кнопка, которая тут есть, благодаря ей вы можете собственно победить, если очистите все души.\n'
                                          'Число онлайна - показывает количество игроков в реальном времени участвующих в игре.\n'
                                          'Приятной игры. Желаем победить!\n\n'
                                          'Designed by maksimator & tunknowng <3')
        bot.send_message(message.chat.id, 'Давай тебя зарегаем. Напиши свое ФИО')
        bot.register_next_step_handler(message, get_username)


@bot.message_handler(commands=['admin'])
def adminstration(message):
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    admin = cur.execute("SELECT * FROM admins WHERE chat_id = ?",
                         (message.chat.id,)).fetchone()
    cur.close()
    conn.close()
    if admin:
        markup1 = types.InlineKeyboardMarkup()
        list_info = types.InlineKeyboardButton("Список", callback_data='list_info')
        delete_admin = types.InlineKeyboardButton("Удалить админа", callback_data='delete_admin')
        markup1.row(list_info, delete_admin)
        user_ban = types.InlineKeyboardButton("Дисквалифицировать участника", callback_data='user_ban')
        markup1.row(user_ban)
        bot.reply_to(message, "Добро пожаловать в администрирование игры", reply_markup=markup1)

cancel_status = {}


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'list_info':
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users')
        users = cur.fetchall()
        info = 'Чистые души\n'
        for el in users:
            info += f'Имя: {el[1]}, Направление: {el[2]}, Код: {el[3]}, Цель: {el[4]}\n'

        cur.execute('SELECT * FROM selected_users')
        users = cur.fetchall()
        info += '\nСвязаные души\n'

        for el in users:
            info += f'Имя: {el[1]}, Направление: {el[2]}, Код: {el[3]}, Цель: {el[4]}\n'

        cur.execute('SELECT * FROM admins')
        users = cur.fetchall()
        info += '\nadmins\n'

        for el in users:
            info += f'Имя: {el[1]}, Код: {el[2]}\n'

        cur.close()
        conn.close()

        bot.send_message(call.message.chat.id, info)

    elif call.data == 'delete_admin':
        cancel_status[call.message.chat.id] = False

        keyboard_delete_admin = types.InlineKeyboardMarkup()
        cancel_btn = types.InlineKeyboardButton("Отмена", callback_data='cancel_delete_admin')
        keyboard_delete_admin.row(cancel_btn)

        bot.send_message(call.message.chat.id, 'Напиши код админа:', reply_markup=keyboard_delete_admin)
        bot.register_next_step_handler(call.message, delete_adn)

    elif call.data == 'user_ban':
        cancel_status[call.message.chat.id] = False

        keyboard_delete_user = types.InlineKeyboardMarkup()
        cancel_btn = types.InlineKeyboardButton("Отмена", callback_data='cancel_delete_user')
        keyboard_delete_user.row(cancel_btn)

        bot.send_message(call.message.chat.id, 'Введите его код:', reply_markup=keyboard_delete_user)
        bot.register_next_step_handler(call.message, user_ban)

    elif call.data == "cancel_delete_admin":
        bot.send_message(call.message.chat.id, 'Удаление админа отменено', reply_markup=None)
        cancel_status[call.message.chat.id] = True

    elif call.data == "cancel_delete_user":
        bot.send_message(call.message.chat.id, 'Дисквалификация игрока отменена', reply_markup=None)
        cancel_status[call.message.chat.id] = True

    elif call.data == "cancel_soul_clean":
        bot.send_message(call.message.chat.id, 'Очистка души отменена', reply_markup=None)
        cancel_status[call.message.chat.id] = True


def delete_adn(message):
    if cancel_status[message.chat.id]:
        cancel_status[message.chat.id] = False
        return

    bot.send_message(message.text.strip(), 'Вас исключили из администраторов')
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    cur.execute('DELETE FROM admins WHERE chat_id = ?',
                    (message.text.strip(),))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, 'Админ исключен')


def user_ban(message):
    if cancel_status[message.chat.id]:
        cancel_status[message.chat.id] = False
        return

    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    exists = (cur.execute("SELECT * FROM users WHERE chat_id = ?",
                          (message.text.strip(),))).fetchone()
    cur.close()
    conn.close()

    if exists:
        bot.send_message(message.text.strip(), 'Вас дисквалифицировали')
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE chat_id = ?',
                    (message.text.strip(),))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        exists_sel = (cur.execute("SELECT * FROM selected_users WHERE chat_id = ?",
                                  (message.text.strip(),))).fetchone()
        cur.close()
        conn.close()

        if exists_sel:
            bot.send_message(message.text.strip(), 'Вас дисквалифицировали')

            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()
            cur.execute('DELETE FROM selected_users WHERE chat_id = ?',
                        (message.text.strip(),))
            conn.commit()
            cur.close()
            conn.close()
        else:
            bot.send_message(message.chat.id, "Проверьте правильность введенного кода игрока. И повторите попытку")
            return

    bot.send_message(message.chat.id, 'Игрок дисквалифицирован')


# Функция для получения имени пользователя и его регистрации
def get_username(message):
    name = message.text  # Имя пользователя, которое он отправил

    if (name == 'Правила') or (name == 'Моя цель') or (name == 'Очистить душу') or (name == 'Число онлайна') or (name == '/start'):
        bot.send_message(message.chat.id, "Что-то не то, попробуем еще раз. Напиши свое ФИО")
        bot.register_next_step_handler(message, get_username)
    else:
        bot.send_message(message.chat.id, "Отлично! И мне нужно еще твое направление")
        bot.register_next_step_handler(message, get_user_mean, name)


# Функция для получения направления пользователя и его регистрации
def get_user_mean(message, name):
    mean = message.text

    if (mean == 'Правила') or (mean == 'Моя цель') or (mean == 'Очистить душу') or (mean == 'Число онлайна') or (mean == '/start'):
        bot.send_message(message.chat.id, "Что-то не то, попробуем еще раз. Напиши своё направление")
        bot.register_next_step_handler(message, get_user_mean, name)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        chat_id = message.chat.id
        if mean == 'Админ':
            bot.send_message(message.chat.id, f"Введите пароль")
            bot.register_next_step_handler(message, pass_word, name)
        else:
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


async def register_admin(name: str, chat_id: str):
    async with aiosqlite.connect('Killer.sql') as db:
        await db.execute(
            "INSERT INTO admins (name, chat_id) VALUES (?, ?)",
            (name, chat_id)
        )
        await db.commit()


def pass_word(message, name):
    password_from_user = message.text

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    chat_id = message.chat.id

    if password_from_user == Pass_Word:
        loop.run_until_complete(register_admin(name, chat_id))
        bot.send_message(message.chat.id, "Вы успешно зарегестрированы, как админ")
    else:
        bot.send_message(message.chat.id, "Вы не являетесь доверенным лицом")


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
                    bot.send_message(message.chat.id, f"У вас уже был закреплен пользователь, но его душа исчезла")

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
                    bot.send_message(message.chat.id, f"У вас уже был закреплен пользователь, но его душа исчезла")

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
        bot.send_message(message.chat.id, 'Правила:\n'
                                          'Вы должны пройти регистрацию написав свое ФИО!!, а так же свое направление(ИТ, РИТ и т.п.).\n'
                                          'Смысл игры заключается в том, чтобы очистить все души и остаться последней душой.\n'
                                          'У вас есть 4 кнопки для управления игрой:\n'
                                          '"Моя цель" - при нажатии выводит вашу действующую цель, которую вы должны найти и очистить.\n'
                                          'Для того, чтобы очистить душу вам следует найти этого человека в реальной жизни и спросить у него его код, '
                                          'который понадобиться для очищения, а также для доказательства нужно будет сфотографироваться с очищенной душой и отправить по ссылке админу (@aokom02) для проверки.\n'
                                          'После чего вам будет доступна новая цель.\n'
                                          'Правила - при нажатии выводит эти самые правила, чтобы еще раз с ними ознакомиться, если вы вдруг забыли.\n'
                                          'Очистить душу - самая главная кнопка, которая тут есть, благодаря ей вы можете собственно победить, если очистите все души.\n'
                                          'Число онлайна - показывает количество игроков в реальном времени участвующих в игре.\n'
                                          'Приятной игры. Желаем победить!\n\n'
                                          'Designed by maksimator & tunknowng <3')
    elif message.text == 'Очистить душу':
        cancel_status[message.chat.id] = False

        keyboard_cancel = types.InlineKeyboardMarkup()
        cancel_btn = types.InlineKeyboardButton("Отмена", callback_data='cancel_soul_clean')
        keyboard_cancel.row(cancel_btn)

        bot.send_message(message.chat.id, 'Введите кодовое слово', reply_markup=keyboard_cancel)
        bot.register_next_step_handler(message, move_to_bin)
    elif message.text == 'Число онлайна':
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        total_users = len(cur.execute('SELECT * FROM users').fetchall()) + len(cur.execute('SELECT * FROM selected_users').fetchall())
        cur.close()
        conn.close()

        if (total_users % 10 == 1) and (total_users != 11):
            bot.send_message(message.chat.id, f"Сейчас в игре {total_users} душа")
        elif (total_users % 10 in range(2, 5)) and (total_users not in range(12, 15)):
            bot.send_message(message.chat.id, f"Сейчас в игре {total_users} души")
        else:
            bot.send_message(message.chat.id, f"Сейчас в игре {total_users} душ")


def move_to_bin(message):
    if cancel_status[message.chat.id]:
        cancel_status[message.chat.id] = False
        return

    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    user = cur.execute("SELECT * FROM users WHERE chat_id = ?",
                       (message.chat.id,)).fetchone()
    cur.close()
    conn.close()

    if user:
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute("UPDATE users SET target_id = ? WHERE chat_id = ?",
                    (None, message.chat.id,))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute("UPDATE selected_users SET target_id = ? WHERE chat_id = ?",
                    (None, message.chat.id,))
        conn.commit()
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

    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    exists = (cur.execute("SELECT * FROM users")).fetchall()
    exists_sel = (cur.execute("SELECT * FROM selected_users").fetchall())
    cur.close()
    conn.close()

    if (len(exists_sel) + len(exists)) == 1:
        bot.send_message(message.chat.id, 'Вы победитель. Поздравляю!!!')
    else:
        bot.send_message(message.chat.id,f"Душа очищена")
        select_users(message)


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

            selected_user = list[4]
            while True:
                selected_user = copy.deepcopy(random.choice(info))

                conn = sqlite3.connect('Killer.sql')
                cur = conn.cursor()
                targeting_users = cur.execute('SELECT * FROM selected_users WHERE NOT target_id = ?',
                                             (selected_user[2],)).fetchall()
                cur.close()
                conn.close()

                if not targeting_users:
                    break

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
            bot.send_message(message.chat.id, 'Нет свободной души')


bot.polling(none_stop=True)
