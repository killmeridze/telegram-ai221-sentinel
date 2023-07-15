import telebot
import datetime
from time import sleep
import json
import sqlite3
from threading import Thread
import schedule as sc
import settings
from loguru import logger
from dotenv import load_dotenv
import os



logger.add('logging.log', format='{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}', level='DEBUG', rotation='10 MB', compression='zip')

load_dotenv()

TOKEN = os.getenv('TOKEN')
ADMINS = [int(admin) for admin in os.getenv('ADMINS').split(',')]
with open('button_texts.json', 'r', encoding='utf-8') as file:
    BUTTON_TEXTS = json.load(file)

bot = telebot.TeleBot(TOKEN)

def schedule_checker() -> None:
    while True:
        sc.run_pending()
        sleep(1)

def schedule_text(today: datetime.date, language: str) -> str:
    '''Функция для составления сообщения с расписанием'''

    day_name_en = today.strftime('%A').lower()
    day_name_ru = settings.weekday_name_ru_dict.get(day_name_en, day_name_en)
    day_name_uk = settings.weekday_name_uk_dict.get(day_name_en, day_name_en)

    schedule_file = f'{language}_schedule.json'
    
    with open(schedule_file, 'r', encoding='utf-8') as file:
        schedule = json.load(file).get(day_name_en)

    if language == 'rus':
        if not schedule:
            message_text = 'Ты бессмертн(-ый/-ая), что ли? Иди проспись'
            return message_text

        message_text = f'Расписание на {day_name_ru}:\n\n'
    else:
        if not schedule:
            message_text = "Нема що робити? Краще іди поспи"
            return message_text

        message_text = f'Розклад на {day_name_uk}:\n\n'

    # Проверка на чётность/нечётность False - нечётная, True - чётная
    current_week_number = today.isocalendar()[1]
    week_parity = False
    if (current_week_number - settings.FIRST_WEEK_NUMBER) % 2 == 0:
        week_parity = False
    else:
        week_parity = True
    
    for item in schedule:
        if item.get("week_parity") is None or item.get("week_parity") is week_parity:
            message_text += f'{item["time"]}{item["name"]}:\n'
            for link in item["links"]:
                message_text += f'{link}\n'

    return message_text


def send_schedule() -> None:
    '''Функция для авторассылки сообщений'''

    today = datetime.date.today()

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute("""SELECT user_id, language FROM subscriptions WHERE subscribed == 1""")
    subscribers = cursor.fetchall()

    conn.commit()
    conn.close()

    for subscriber in subscribers:
        try:
            message_text = schedule_text(today, subscriber[1])
            bot.send_message(chat_id=subscriber[0], text=message_text)
            logger.info(f'Sent schedule to user_id - {subscriber[0]} via autosending')
        except telebot.apihelper.ApiException as e:
            logger.warning(f'Failed to send a schedule to user with user_id - {subscriber[0]}: {e}')


def get_user_language(chat_id: int) -> str:
    '''Функция для получения языка пользователя'''

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute("""SELECT language FROM subscriptions WHERE user_id == ?""", (chat_id, ))
    language = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return language

def update_buttons(language: str, is_admin: int) -> None:
    '''Функция для обновления кнопок в соответствии с языком пользователя'''

    button = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["schedule"])
    button_tomorrow = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["schedule_tomorrow"])
    button_subscribe = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["subscribe"])
    button_unsubscribe = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["unsubscribe"])
    button_change_language = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["change_language"])
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(button, button_tomorrow)
    keyboard.row(button_subscribe, button_unsubscribe, button_change_language)

    if is_admin:
        button_send_all = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["send_all"])
        keyboard.row(button_send_all)

    return keyboard



@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f'New user - {message.from_user.username}')

    username = message.chat.username
    user_id = message.chat.id
    subscribed = 0
    language = 'rus'
    is_admin = 0

    if user_id in ADMINS:
        is_admin = 1

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS subscriptions
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                user_id INTEGER NOT NULL,
                subscribed INTEGER NOT NULL CHECK (subscribed IN (0, 1)),
                language TEXT NOT NULL CHECK (language IN ('rus', 'ukr')),
                is_admin INTEGER NOT NULL CHECK (is_admin IN (0, 1)))""")

    cursor.execute("""SELECT * FROM subscriptions WHERE user_id == ?""", (user_id, ))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.execute("""UPDATE subscriptions 
                    SET username = ?, subscribed = ?, language = ?, is_admin = ? 
                    WHERE user_id == ?""",
                    (username, subscribed, language, is_admin, user_id))
    else:
        cursor.execute("""INSERT INTO subscriptions (username, user_id, subscribed, language, is_admin) VALUES (?, ?, ?, ?, ?)""",
                    (username, user_id, subscribed, language, is_admin))
    
    conn.commit()
    conn.close()

    keyboard = update_buttons(language, is_admin)

    bot.send_message(chat_id=message.chat.id, text=BUTTON_TEXTS[language]["welcome_message"], reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in ['Расписание', 'Розклад'], content_types=['text'])
def schedule(message):
    today = datetime.date.today()
    user_language = get_user_language(message.chat.id)
    message_text = schedule_text(today, user_language)

    bot.send_message(chat_id=message.chat.id, text=message_text)
    logger.info(f'Sent schedule to {message.from_user.username}(user_id - {message.from_user.id}) via command "{message.text}"')

@bot.message_handler(func=lambda message: message.text in ['Расписание на завтра', 'Розклад на завтра'], content_types=['text'])
def schedule_tomorrow(message):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    user_language = get_user_language(message.chat.id)
    message_text = schedule_text(tomorrow, user_language)

    bot.send_message(chat_id=message.chat.id, text=message_text)
    logger.info(f'Sent schedule to {message.from_user.username}(user_id - {message.from_user.id}) via command "{message.text}"')

@bot.message_handler(func=lambda message: message.text in ['Подписаться', 'Підписатися'], content_types=['text'])
def subscribe(message):
    user_language = get_user_language(message.chat.id)

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute("""SELECT subscribed FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
    subscribed = cursor.fetchone()[0]

    logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) tried to subscribe')
    if subscribed:
        bot.reply_to(message, 'Вы уже подписаны на рассылку!' if user_language == 'rus' else 'Ви вже підписані на розсилку!')
        logger.info(f"User {message.from_user.username}(user_id - {message.from_user.id}) has been already subscribed")
    else:
        cursor.execute("""UPDATE subscriptions SET subscribed = 1 WHERE user_id == ?""", (message.chat.id, ))
        conn.commit()
        bot.reply_to(message, 'Вы успешно подписались на рассылку!' if user_language == 'rus' else 'Ви успішно підписалися на розсилку!')
        logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) has successfully subscribed')

    conn.close()

@bot.message_handler(func=lambda message: message.text in ['Отписаться', 'Відписатися'], content_types=['text'])
def unsubscribe(message):
    user_language = get_user_language(message.chat.id)

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute("""SELECT subscribed FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
    subscribed = cursor.fetchone()[0]

    logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) tried to unsubscribe')
    if not subscribed:
        bot.reply_to(message, 'Вы не подписаны на рассылку!' if user_language == 'rus' else 'Ви не підписані на розсилку!')
        logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) has been already unsubscribed')
    else:
        cursor.execute("""UPDATE subscriptions SET subscribed = 0 WHERE user_id == ?""", (message.chat.id, ))
        conn.commit()
        bot.reply_to(message, 'Вы успешно отписались от рассылки!' if user_language == 'rus' else 'Ви успішно відписалися від розсилки!')
        logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) has successfully unsubscribed')

    conn.close()

@bot.message_handler(func=lambda message: message.text in ['Сделать рассылку', 'Зробити розсилку'], content_types=['text'])
def get_text_to_send_all(message):
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    
    cursor.execute("""SELECT is_admin, language FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
    user_is_admin, user_language = cursor.fetchone()
    
    conn.commit()
    conn.close()

    logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) tried to send all')
    if not user_is_admin:
        bot.reply_to(message, 'У вас нет прав на это' if user_language == 'rus' else 'У вас нема прав для цього')
        logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) has no rights to send all')
        return
    
    msg = bot.reply_to(message, 'Что вы хотите отправить всем?' if user_language == 'rus' else 'Що ви хочете відправити усім?')

    bot.register_next_step_handler(msg, send_all)

def send_all(message):
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    
    cursor.execute("""SELECT language FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
    user_language = cursor.fetchone()[0]

    conn.commit()

    cursor.execute("""SELECT user_id FROM subscriptions""")
    users_ids = cursor.fetchall()

    conn.commit()
    conn.close()
    
    successful_sends = 0
    total_users = 0

    for user_id in users_ids:
        if user_id[0] == message.chat.id:
            continue
        try:
            bot.send_message(user_id[0], message.text)
            logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) sent "{message.text}" to {user_id[0]} via send all command')
            successful_sends += 1
        except telebot.apihelper.ApiException as e:
            logger.warning(f'Failed to send a message to user with user_id - {user_id}: {e}')
        total_users += 1
    
    bot.reply_to(message, f'Сообщение отправлено {successful_sends} из {total_users} пользователей:\n{message.text}' if user_language == 'rus'
                else f'Повідмлення відправлене {successful_sends} з {total_users} користувачів:\n{message.text}')

@bot.message_handler(func=lambda message: message.text in ['Поменять язык', 'Змінити мову'], content_types=['text'])
def change_language(message):
    user_language = get_user_language(message.chat.id)
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    rus_lang = telebot.types.InlineKeyboardButton(text='Русский' if user_language == 'rus' else 'Російська', callback_data='rus')
    ukr_lang = telebot.types.InlineKeyboardButton(text="Украинский" if user_language == 'rus' else 'Українська', callback_data='ukr')

    keyboard.add(rus_lang, ukr_lang)

    bot.send_message(message.chat.id, 'На какой язык поменять?' if user_language == 'rus' else 'На яку мову змінити?', reply_markup=keyboard)
    logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) tried to change language')

@bot.callback_query_handler(func=lambda call: True)
def answer_change_language(call):
    user_language = get_user_language(call.message.chat.id)

    if call.data == 'rus':
        if user_language == 'rus':
            bot.answer_callback_query(call.id, 'Этот язык уже выбран')
            logger.info(f'User {call.message.chat.username}(user_id - {call.message.chat.id}) already has russian language')
            return
        
        conn = sqlite3.connect('subscriptions.db')
        cursor = conn.cursor()

        cursor.execute("""UPDATE subscriptions SET language = 'rus' WHERE user_id == ?""", (call.message.chat.id, ))
        conn.commit()
        
        cursor.execute("""SELECT is_admin FROM subscriptions WHERE user_id == ?""", (call.message.chat.id, ))
        is_admin = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        bot.answer_callback_query(call.id, 'Язык изменён')
        
        keyboard = update_buttons('rus', is_admin)

        logger.info(f'User {call.message.chat.username}(user_id - {call.message.chat.id}) changed language to russian')

        bot.send_message(chat_id=call.message.chat.id, text='Сейчас выбран русский язык', reply_markup=keyboard)

    else:
        if user_language == 'ukr':
            bot.answer_callback_query(call.id, 'Ця мова вже обрана')
            logger.info(f'User {call.message.chat.username}(user_id - {call.message.chat.id}) already has ukrainian language')
            return
        
        conn = sqlite3.connect('subscriptions.db')
        cursor = conn.cursor()
        
        cursor.execute("""UPDATE subscriptions SET language = 'ukr' WHERE user_id == ?""", (call.message.chat.id, ))
        conn.commit()
        
        cursor.execute("""SELECT is_admin FROM subscriptions WHERE user_id == ?""", (call.message.chat.id, ))
        is_admin = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, 'Мову змінено')
        
        keyboard = update_buttons('ukr', is_admin)
        
        logger.info(f'User {call.message.chat.username}(user_id - {call.message.chat.id}) changed language to ukrainian')

        bot.send_message(chat_id=call.message.chat.id, text='Зараз обрана українська мова', reply_markup=keyboard)

    bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.message_id, reply_markup='')



if __name__ == '__main__':
    sc.every().monday.at('07:00').do(send_schedule)
    sc.every().tuesday.at('07:00').do(send_schedule)
    sc.every().wednesday.at('07:00').do(send_schedule)
    sc.every().thursday.at('07:00').do(send_schedule)
    sc.every().friday.at('07:00').do(send_schedule)

    thread = Thread(target=schedule_checker, daemon=True)
    thread.start()

    bot.polling(none_stop=True)

    while thread.is_alive:                              
        thread.join(1)
