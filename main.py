import telebot
import datetime
import json
import settings
import sqlite3
from threading import Thread
import schedule as sc
from time import sleep

bot = telebot.TeleBot('5844782786:AAGqpYHZMmRZ3sfWdoGioA8FODBweFEG-eA')

def send_schedule():
    message_text = "Приветики"
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM subscriptions')
    subscribers = cursor.fetchall()

    for subscriber in subscribers:
        bot.send_message(chat_id=subscriber[0], text=message_text)

    conn.commit()
    conn.close()

def schedule_checker():
    while True:
        sc.run_pending()
        sleep(1)
        

@bot.message_handler(commands=['start'])
def start(message):
    button = telebot.types.KeyboardButton('/Расписание')
    button_subscribe = telebot.types.KeyboardButton('/Подписаться')
    button_unsubscribe = telebot.types.KeyboardButton('/Отписаться')
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(button)
    keyboard.row(button_subscribe, button_unsubscribe)
    bot.send_message(chat_id=message.chat.id, text=f'Привет, сливка! Нажми на кнопку, чтобы получить расписание!', reply_markup=keyboard)

@bot.message_handler(commands=['Расписание'])
def schedule(message):
    today = datetime.date.today()

    #Проверка на чётность/нечётность False - нечётная, True - чётная
    current_week_number = today.isocalendar()[1]
    week_parity = False
    if (current_week_number - settings.FIRST_WEEK_NUMBER) % 2 == 0:
        week_parity = False
    else:
        week_parity = True
    
    day_name_en = today.strftime('%A').lower()
    day_name_ru = settings.weekday_name_ru_dict.get(day_name_en, day_name_en)

    with open('schedule.json', 'r', encoding='utf-8') as f:
        schedule = json.load(f).get(day_name_en)

    if not schedule:
        bot.send_message(chat_id=message.chat.id, text="Ты бессмертн(-ый/-ая) что ли? Иди проспись")
        return

    message_text = f"Расписание на {day_name_ru}:\n\n"

    for item in schedule:
        if item.get('week_parity') is None:
            message_text += f"{item['time']}{item['name']}:\n"
            for link in item["links"]:
                message_text += f"{link}\n"

        elif item.get('week_parity') is week_parity:
            message_text += f"{item['time']}{item['name']}:\n"
            for link in item["links"]:
                message_text += f"{link}\n"

    bot.send_message(chat_id=message.chat.id, text=message_text)

@bot.message_handler(commands=['Подписаться'])
def subscribe(message):
    user_id = message.chat.id
    subscription_time = datetime.datetime.now()
    
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   user_id INTEGER NOT NULL, 
                   subscription_time TEXT NOT NULL)''')

    cursor.execute('SELECT user_id FROM subscriptions WHERE user_id = ?', (user_id,))
    subscribe_user = cursor.fetchone()

    if subscribe_user:
        conn.commit()
        bot.reply_to(message, "Вы уже подписаны на рассылку!")
    else:
        cursor.execute('INSERT INTO subscriptions (user_id, subscription_time) VALUES (?, ?)', (user_id, subscription_time))
        conn.commit()
        bot.reply_to(message, "Вы успешно подписались на рассылку!")

    conn.close()

@bot.message_handler(func=lambda message: True, content_types=['text'])
def unsubscribe(message):
    user_id = message.chat.id
    subscription_time = datetime.datetime.now()
    
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM subscriptions WHERE user_id = ?', (user_id,))
    unsubscribe_user = cursor.fetchone()

    if unsubscribe_user:
        cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
        conn.commit()
        bot.reply_to(message, "Вы успешно отписались от рассылки!")
    else:
        conn.commit()
        bot.reply_to(message, "Вы не подписаны на рассылку!")

    conn.close()

if __name__ == '__main__':
    sc.every(3).seconds.do(send_schedule)
    # sc.every().day.at("07:00").do(send_schedule)
    Thread(target=schedule_checker).start()
    bot.polling(none_stop=True)
