import telebot
from telebot import types
import sqlite3
import random

bot = telebot.TeleBot('7256424127:AAEHDa-kBRz56QTnY5kP3cUomUf-S8wX0ac')
name = None

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
    Bin = types.KeyboardButton('Захватить душу')
    List = types.KeyboardButton('Список')
    markup.row(Bin, List)
    bot.send_message(message.chat.id, f'Приветствую, {message.from_user.first_name}!\nТы попал на игру "Ловец душ" от МТУСИ', reply_markup=markup)
    bot.send_message(message.chat.id, 'Давай тебя зарегаем. Напиши свое ФИО')
    bot.register_next_step_handler(message, user_name)


def user_name(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, 'И свое направление')
    bot.register_next_step_handler(message, user_mean)

def user_mean(message):
    mean = message.text.strip()
    conn = sqlite3.connect('Killer.sql')
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, mean, chat_id) VALUES ('%s', '%s', '%s')" % (name, mean, message.from_user.id))
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, f'Ты зареган\nТвое кодовое слово: {message.from_user.id}')#, reply_markup=markup1)

@bot.message_handler(content_types=['text'])
def send(message):
    if message.text == 'Моя цель':
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        exists = cur.execute("SELECT * FROM users WHERE chat_id = ?", (message.from_user.id,)).fetchone()
        cur.close()
        conn.close()
        if exists:
            bot.send_message(message.chat.id, 'erdbjengmbkslndkf')
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()

            # Проверяем, есть ли у текущего пользователя уже закрепленный пользователь
            cur.execute("SELECT target_id FROM users WHERE chat_id = ?", (message.from_user.id,))
            target_id_row = cur.fetchone()

            if target_id_row[0]:
                #cur.execute("SELECT name, mean FROM users WHERE chat_id = ?", (target_id_row[0],))
                #assigned_user = cur.fetchone()

                #if assigned_user:
                    name, mean = assigned_user
                    bot.send_message(message.chat.id, f"У вас уже закреплен пользователь: {name}, направление: {mean}")
            else:
                select_users(message)

            cur.close()
            conn.close()
        else:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()

            # Проверяем, есть ли у текущего пользователя уже закрепленный пользователь
            cur.execute("SELECT target_id FROM users WHERE chat_id = ?", (message.from_user.id,))
            target_id_row = cur.fetchone()
            bot.send_message(message.chat.id, '15615616162')
            if target_id_row and target_id_row[0]:

                target_id = target_id_row[0]
                cur.execute("SELECT name, mean FROM users WHERE chat_id = ?", (target_id,))
                assigned_user = cur.fetchone()

                if assigned_user:
                    name, mean = assigned_user
                    bot.send_message(message.chat.id, f"У вас уже закреплен пользователь: {name}, направление: {mean}")
                else:
                    select_users(message)

            cur.close()
            conn.close()

    elif message.text == 'Правила':
        bot.send_message(message.chat.id, 'Правила:')
    elif message.text == 'Захватить душу':
        bot.send_message(message.chat.id, 'Введите кодовое слово')
        bot.register_next_step_handler(message, move_to_bin)
    elif message.text == 'Список':
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users')
        users = cur.fetchall()
        info = 'Доступные души\n'
        for el in users:
            info += f'Имя: {el[1]}, Направление: {el[2]},  {el[4]}\n'

        cur.execute('SELECT * FROM selected_users')
        users = cur.fetchall()
        info += '\nНедоступные души\n'
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

    cur.execute('SELECT * FROM selected_users')
    select_users = cur.fetchall()
    select_user_id = tuple([user[3] for user in select_users])
    select_user_id += (message.from_user.id,)
    if select_user_id:
        query = f'SELECT * FROM users WHERE id NOT IN ({",".join("?" for _ in select_user_id)})'
        cur.execute(query, select_user_id)
    else:
        cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    cur.close()
    conn.close()

    if len(users) > 0 :
        info = [[0 for j in range(4)] for i in range(len(users))]
        line = 0
        for el1 in users:
            info[line][0] = f'{el1[1]}'
            info[line][1] = f'{el1[2]}'
            info[line][2] = f'{el1[3]}'
            info[line][3] = f'{el1[4]}'
            line += 1

        selected_user = random.choice(info)
        bot.send_message(message.chat.id, f'Имя: {selected_user[0]}\nНаправление: {selected_user[1]}')
        conn = sqlite3.connect('Killer.sql')
        cur = conn.cursor()
        cur.execute("INSERT INTO selected_users (name, mean, chat_id, target_id) VALUES ('%s', '%s', '%s', '%s')" % (selected_user[0], selected_user[1], selected_user[2], selected_user[3]))
        conn.commit()
        chat_id = selected_user[2]
        exists = cur.execute("SELECT 1 FROM users WHERE id = ?", [message.from_user.id]).fetchone()
        cur.close()
        conn.close()
        if exists:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()

            cur.execute("UPDATE users SET target_id = ? WHERE chat_id = ?", (message.from_user.id,chat_id,))

            conn.commit()
            cur.close()
            conn.close()
        else:
            conn = sqlite3.connect('Killer.sql')
            cur = conn.cursor()

            cur.execute("UPDATE selected_users SET target_id = ? WHERE chat_id = ?", (chat_id,message.from_user.id,))

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
        bot.send_message(message.chat.id, 'Введите кодовое слово')


bot.polling(none_stop=True)
