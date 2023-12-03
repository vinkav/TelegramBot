import telebot
from telebot import types
import sqlite3
import time as tm
import datetime
from datetime import datetime

name_usr = ''
type_usr = ''

bot = telebot.TeleBot('6867311404:AAEod47Y0Oo0HecusOcBdxhIyXiaUX-28TI')

@bot.message_handler(commands = ['start'])
def start(message):
    conn = sqlite3.connect('bd.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users(id int primary key, name_user varchar(70), type_user varchar(10), class int)')
    cur.execute('CREATE TABLE IF NOT EXISTS visit(day_visit date, name_user varchar(70), class int)')
    conn.commit()
    cur.close()
    conn.close()

    registration(message)
    report(message)


def registration(message):
    conn = sqlite3.connect('bd.sql')
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = '%d'" % (message.from_user.id))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, 'Розпочнемо реєстрацію! Введіть ваше ПІБ')
    bot.register_next_step_handler(message, name_user)

def name_user(message):
    global name_usr
    name_usr = message.text.strip()

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Вчитель', callback_data='teacher')
    btn2 = types.InlineKeyboardButton('Учень', callback_data='student')
    markup.row(btn1, btn2)
    bot.send_message(message.chat.id, 'Ви вчитель чи учень?', reply_markup=markup)

def class_user(message):
    conn = sqlite3.connect('bd.sql')
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE id = '%d'" % (message.from_user.id))
    conn.commit()

    cur.execute("SELECT class FROM users WHERE class = '%d'" % (message.from_user.id))
    flag = False
    class_usr = cur.fetchall()
    for cl_usr in class_usr:
        flag = True
        break

    if flag:
        cur.execute("INSERT INTO users (id, name_user, type_user, class) VALUES('%d', '%s', '%s', '%d')" % (
        message.from_user.id, name_usr, 'учень', int(message.text.replace(' ', '').replace(' ', ''))))
        conn.commit()
        cur.close()
        conn.close()
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Відвідати уроки', callback_data='visit')
        btn2 = types.InlineKeyboardButton('Переєструватись', callback_data='registry')
        markup.row(btn1, btn2)
        bot.send_message(message.chat.id, 'Реєстрація успішна!', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Клас не знайдено! Введіть код класу')
        bot.register_next_step_handler(call.message, class_user)

def report(message):
    conn = sqlite3.connect('bd.sql')
    cur = conn.cursor()
    cur.execute("SELECT type_user FROM users WHERE id = '%s'" % (message.from_user.id))
    type_users = cur.fetchall()
    is_teacher = None
    for tp_usr in type_users:
        if tp_usr[0] == 'вчитель':
            is_teacher = True
        if tp_usr[0] == 'учень':
            is_teacher = False
    cur.close()
    conn.close()
    if is_teacher is not None:
        while True:
            time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                            datetime.now().minute, datetime.now().second)
            if is_teacher:
                if time.hour == 18 and time.minute == 0 and time.second == 0:
                    conn = sqlite3.connect('bd.sql')
                    cur = conn.cursor()
                    cur.execute("SELECT name_user FROM visit WHERE class = '%d' AND DATE(day_visit) = DATE(datetime('now'))" % (message.from_user.id))
                    users = cur.fetchall()
                    text = datetime.now().strftime("%d.%m.%Y") + '\n'
                    for el in users:
                        text += f'{el[0]}\n'
                    cur.close()
                    conn.close()
                    bot.send_message(message.chat.id, text)
                    tm.sleep(60)
            elif time.hour == 7 and time.minute == 55 and time.second == 0:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Відвідати уроки', callback_data='visit')
                btn2 = types.InlineKeyboardButton('Переєструватись', callback_data='registry')
                markup.row(btn1, btn2)
                bot.send_message(message.chat.id, 'Відвідування уроків:', reply_markup=markup)
                tm.sleep(60)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == 'visit':
        conn = sqlite3.connect('bd.sql')
        cur = conn.cursor()
        cur.execute("SELECT name_user, class FROM users WHERE id = '%d'" % (call.from_user.id))
        students = cur.fetchall()
        for el in students:
            cur.execute("INSERT INTO visit (day_visit, name_user, class) VALUES(DATE(datetime('now')), '%s', '%d')" % (el[0], call.from_user.id))
        conn.commit()
        cur.close()
        conn.close()
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Переєструватись', callback_data='registry')
        markup.row(btn1)
        bot.send_message(call.message.chat.id, 'Присутність відмічена!', reply_markup=markup)
        call.message.from_user.id = call.from_user.id
        report(call.message)
    elif call.data == 'teacher':
        conn = sqlite3.connect('bd.sql')
        cur = conn.cursor()

        cur.execute("DELETE FROM users WHERE id = '%d'" % (call.from_user.id))
        conn.commit()

        cur.execute("INSERT INTO users (id, name_user, type_user, class) VALUES('%d', '%s', '%s', '%d')" % (call.from_user.id, name_usr, 'вчитель', call.from_user.id))
        conn.commit()
        cur.close()
        conn.close()
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Переєструватись', callback_data='registry')
        markup.row(btn1)
        bot.send_message(call.message.chat.id, f'Вас успішно зареєстровано! Код класу: {call.from_user.id}', reply_markup=markup)
        call.message.from_user.id = call.from_user.id
        report(call.message)
    elif call.data == 'student':
        bot.send_message(call.message.chat.id, 'Введіть код класу')
        bot.register_next_step_handler(call.message, class_user)
    elif call.data == 'registry':
        bot.send_message(call.message.chat.id, 'Присутність',)
        call.message.from_user.id = call.from_user.id
        registration(call.message)


bot.polling(none_stop=True)