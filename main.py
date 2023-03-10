import telebot
import datetime
from time import sleep
import json
import sqlite3
from threading import Thread
import schedule as sc
import settings
from loguru import logger



logger.add("logging.log", format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", level="DEBUG", rotation="10 MB", compression="zip")

# bot = telebot.TeleBot('5844782786:AAGqpYHZMmRZ3sfWdoGioA8FODBweFEG-eA') # main bot
bot = telebot.TeleBot('6018459380:AAFRJzPHYea3GxOwEhS3gLzf-L5XxjQQDts') # temp bot

def schedule_checker():
    while True:
        sc.run_pending()
        sleep(1)

def schedule_text(today: datetime.date) -> str:
    """Функция для составления сообщения с расписанием"""

    day_name_en = today.strftime('%A').lower()
    day_name_ru = settings.weekday_name_ru_dict.get(day_name_en, day_name_en)

    with open('schedule.json', 'r', encoding='utf-8') as f:
        schedule = json.load(f).get(day_name_en)

    if not schedule:
        message_text = "Ты бессмертн(-ый/-ая) что ли? Иди проспись"
        return message_text

    message_text = f"Расписание на {day_name_ru}:\n\n"

    #Проверка на чётность/нечётность False - нечётная, True - чётная
    current_week_number = today.isocalendar()[1]
    week_parity = False
    if (current_week_number - settings.FIRST_WEEK_NUMBER) % 2 == 0:
        week_parity = False
    else:
        week_parity = True

    for item in schedule:
        if item.get('week_parity') is None:
            message_text += f"{item['time']}{item['name']}:\n"
            for link in item["links"]:
                message_text += f"{link}\n"

        elif item.get('week_parity') is week_parity:
            message_text += f"{item['time']}{item['name']}:\n"
            for link in item["links"]:
                message_text += f"{link}\n"

    return message_text

def send_schedule():
    """Функция для авторассылки сообщений"""
    today = datetime.date.today()
    
    message_text = schedule_text(today)

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM subscriptions')
    subscribers = cursor.fetchall()

    for subscriber in subscribers:
        bot.send_message(chat_id=subscriber[0], text=message_text)
        logger.info(f"Sent schedule to user_id - {subscriber[0]} via autosending")

    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    button = telebot.types.KeyboardButton('Расписание')
    button_subscribe = telebot.types.KeyboardButton('Подписаться')
    button_unsubscribe = telebot.types.KeyboardButton('Отписаться')
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(button)
    keyboard.row(button_subscribe, button_unsubscribe)
    bot.send_message(chat_id=message.chat.id, text=f'Привет, сливка! Нажми на кнопку, чтобы получить расписание!', reply_markup=keyboard)
    logger.info(f"New user - {message.from_user.username}")

@bot.message_handler(func=lambda message: message.text == 'Расписание', content_types=['text'])
def schedule(message):
    today = datetime.date.today()

    message_text = schedule_text(today)

    bot.send_message(chat_id=message.chat.id, text=message_text)
    logger.info(f"Sent schedule to {message.from_user.username}(user_id - {message.from_user.id}) via command /Расписание")

@bot.message_handler(func=lambda message: message.text == 'Подписаться', content_types=['text'])
def subscribe(message):
    logger.info(f"User {message.from_user.id} tried to subscribe")

    username = message.from_user.username
    user_id = message.chat.id
    subscription_time = datetime.datetime.now()
    group_number = 1 # когда будет реализация запроса на ввод группы - доделаем
    subscribed = 1 # подумать надо xd
    language = 'ukr' # same shit

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                subscription_time TEXT NOT NULL,
                group_number INTEGER NOT NULL CHECK (group_number IN (1, 2)),
                subscribed INTEGER NOT NULL CHECK (subscribed IN (0, 1)),
                language TEXT NOT NULL CHECK (language IN ('rus', 'ukr')))''')


    cursor.execute('SELECT user_id FROM subscriptions WHERE user_id = ?', (user_id,))
    subscribe_user = cursor.fetchone()

    if subscribe_user:
        conn.commit()
        bot.reply_to(message, "Вы уже подписаны на рассылку!")
        logger.info(f"User {message.from_user.username}(user_id - {message.from_user.id}) has been already subscribed")

    else:
        cursor.execute('INSERT INTO subscriptions (username, user_id, group_number, subscribed, language, subscription_time) VALUES (?, ?, ?, ?, ?, ?)',
                (username, user_id, group_number, subscribed, language, subscription_time))
        conn.commit()
        bot.reply_to(message, "Вы успешно подписались на рассылку!")
        logger.info(f"User {message.from_user.username}(user_id - {message.from_user.id}) has successfully subscribed")

    conn.close()

@bot.message_handler(func=lambda message: message.text == 'Отписаться', content_types=['text'])
def unsubscribe(message):
    logger.info(f"User {message.from_user.id} tried to unsubscribe")
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
        logger.info(f"User {message.from_user.username}(user_id - {message.from_user.id}) has successfully unsubscribed")
    else:
        conn.commit()
        bot.reply_to(message, "Вы не подписаны на рассылку!")
        logger.info(f"User {message.from_user.username}(user_id - {message.from_user.id}) has been already unsubscribed")

    conn.close()


if __name__ == '__main__':
    # sc.every().day.at("07:00").do(send_schedule)
    sc.every().monday.at("07:00").do(send_schedule)
    sc.every().tuesday.at("07:00").do(send_schedule)
    sc.every().wednesday.at("07:00").do(send_schedule)
    sc.every().thursday.at("07:00").do(send_schedule)
    sc.every().friday.at("07:00").do(send_schedule)
    

    thread = Thread(target=schedule_checker, daemon=True)
    thread.start()

    bot.polling(none_stop=True)

    while thread.is_alive:                              
        thread.join(1)
