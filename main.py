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
import requests
from telebot.apihelper import ApiTelegramException



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

def schedule_text(today: datetime.date, language: str, group: int) -> str:
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
        if item.get("week_parity") is None or item.get("week_parity") is week_parity and item.get("group") is None or item.get("group") is group:
            message_text += f'{item["time"]}\n{item["name"]}:\n'
            for link in item["links"]:
                message_text += f'{link}\n'
            message_text += f'{item["teachers"]}\n\n'

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
    fetched = cursor.fetchone()
    language = fetched[0] if fetched is not None else "rus"

    conn.commit()
    conn.close()

    return language

def get_user_group(chat_id: int) -> str:
    '''Функция для получения группы пользователя'''

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()

        cursor.execute("""SELECT user_group FROM subscriptions WHERE user_id == ?""", (chat_id, ))
        fetched = cursor.fetchone()
        group = fetched[0] if fetched is not None else 1

    return group

# def update_buttons(language: str, is_admin: int) -> None:
#     '''Функция для обновления кнопок в соответствии с языком пользователя'''

#     button = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["schedule"])
#     button_tomorrow = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["schedule_tomorrow"])
#     button_subscribe = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["subscribe"])
#     button_unsubscribe = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["unsubscribe"])
#     button_change_language = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["change_language"])
#     button_find_sticker = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["find_sticker"])
#     keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
#     keyboard.row(button, button_tomorrow)
#     keyboard.row(button_subscribe, button_unsubscribe, button_change_language)
#     keyboard.row(button_find_sticker)

#     if is_admin:
#         button_send_all = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["send_all"])
#         keyboard.row(button_send_all)

#     return keyboard

def update_buttons(language: str, is_admin = None, mode='main') -> None:
    '''Функция для обновления кнопок в соответствии с языком пользователя и выбранным режимом.'''

    # Главное меню
    if mode == 'main':
        button = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["schedule"])
        button_tomorrow = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["schedule_tomorrow"])
        button_subscribe = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["subscribe"])
        button_unsubscribe = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["unsubscribe"])
        button_find_sticker = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["find_sticker"])
        button_settings = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["settings"])
        
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(button, button_tomorrow)
        keyboard.row(button_subscribe, button_unsubscribe)
        keyboard.row(button_find_sticker, button_settings)

        if is_admin:
            button_send_all = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["send_all"])
            keyboard.row(button_send_all)
    
    # Меню настроек
    elif mode == 'settings':
        button_change_language = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["change_language"])
        button_change_group = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["change_group"])
        button_return = telebot.types.KeyboardButton(BUTTON_TEXTS[language]["return"])

        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(button_change_language, button_change_group)
        keyboard.row(button_return)

    return keyboard

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['settings'])
def show_settings(message):
    user_language = get_user_language(message.chat.id)
    prompt_text = "Выберите действие:" if user_language == "rus" else "Оберіть дію:"
    bot.send_message(message.chat.id, prompt_text, reply_markup=update_buttons(user_language, mode='settings'))

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['return'])
def return_to_main(message):
    user_language = get_user_language(message.chat.id)
    prompt_text = "Что делать дальше? Выбор за тобой, сливка" if user_language == "rus" else "Що робити далi? Вибiр за тобою, слiвка"
    bot.send_message(message.chat.id, prompt_text, reply_markup=update_buttons(user_language, mode='main'))

@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f'New user - {message.from_user.username} ({message.from_user.first_name})')

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
                    is_admin INTEGER NOT NULL CHECK (is_admin IN (0, 1)),
                    user_group INTEGER DEFAULT 1 CHECK (user_group IN (1, 2)))""")

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
    user_group = get_user_group(message.chat.id)
    message_text = schedule_text(today, user_language, user_group)

    bot.send_message(chat_id=message.chat.id, text=message_text)
    logger.info(f'Sent schedule to {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) via command "{message.text}"')

@bot.message_handler(func=lambda message: message.text in ['Расписание на завтра', 'Розклад на завтра'], content_types=['text'])
def schedule_tomorrow(message):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    user_language = get_user_language(message.chat.id)
    user_group = get_user_group(message.chat.id)
    message_text = schedule_text(tomorrow, user_language, user_group)

    bot.send_message(chat_id=message.chat.id, text=message_text)
    logger.info(f'Sent schedule to {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) via command "{message.text}"')

@bot.message_handler(func=lambda message: message.text in ['Подписаться', 'Підписатися'], content_types=['text'])
def subscribe(message):
    user_language = get_user_language(message.chat.id)

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute("""SELECT subscribed FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
    result = cursor.fetchone()

    if result is None:
        subscribed = False
    else:
        subscribed = result[0]

    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to subscribe')
    if subscribed:
        bot.reply_to(message, 'Вы уже подписаны на рассылку!' if user_language == 'rus' else 'Ви вже підписані на розсилку!')
        logger.info(f"User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has been already subscribed")
    else:
        cursor.execute("""UPDATE subscriptions SET subscribed = 1 WHERE user_id == ?""", (message.chat.id, ))
        conn.commit()
        bot.reply_to(message, 'Вы успешно подписались на рассылку!' if user_language == 'rus' else 'Ви успішно підписалися на розсилку!')
        logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has successfully subscribed')

    conn.close()

@bot.message_handler(func=lambda message: message.text in ['Отписаться', 'Відписатися'], content_types=['text'])
def unsubscribe(message):
    user_language = get_user_language(message.chat.id)

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()

    cursor.execute("""SELECT subscribed FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
    result = cursor.fetchone()

    if result is None:
        subscribed = False
    else:
        subscribed = result[0]

    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to unsubscribe')
    if not subscribed:
        bot.reply_to(message, 'Вы не подписаны на рассылку!' if user_language == 'rus' else 'Ви не підписані на розсилку!')
        logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has been already unsubscribed')
    else:
        cursor.execute("""UPDATE subscriptions SET subscribed = 0 WHERE user_id == ?""", (message.chat.id, ))
        conn.commit()
        bot.reply_to(message, 'Вы успешно отписались от рассылки!' if user_language == 'rus' else 'Ви успішно відписалися від розсилки!')
        logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has successfully unsubscribed')

    conn.close()

def get_content_description(message):
    if message.content_type == 'text':
        return f'text "{message.text}"'
    elif message.content_type == 'photo':
        return 'a photo'
    elif message.content_type == 'sticker':
        return 'a sticker'
    elif message.content_type == 'animation':
        return 'an animation'
    elif message.content_type == 'voice':
        return 'a voice message'
    else:
        return 'an unknown content'

@bot.message_handler(func=lambda message: message.text in ['Сделать рассылку', 'Зробити розсилку'], content_types=['text', 'photo', 'sticker', 'animation', 'voice'])
def get_text_to_send_all(message):
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    
    cursor.execute("""SELECT is_admin, language FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
    user_is_admin, user_language = cursor.fetchone()
    
    conn.commit()
    conn.close()

    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to send all')
    if not user_is_admin:
        bot.reply_to(message, 'У вас нет прав на это' if user_language == 'rus' else 'У вас нема прав для цього')
        logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has no rights to send all')
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
            if message.content_type == 'text':
                bot.send_message(user_id[0], message.text)
            elif message.content_type == 'photo':
                photo_id = message.photo[-1].file_id 
                bot.send_photo(user_id[0], photo_id)
            elif message.content_type == 'sticker':
                sticker_id = message.sticker.file_id
                bot.send_sticker(user_id[0], sticker_id)
            elif message.content_type == 'animation':
                animation_id = message.animation.file_id
                bot.send_animation(user_id[0], animation_id)
            elif message.content_type == 'voice':
                voice_id = message.voice.file_id
                bot.send_voice(user_id[0], voice_id)
            content_description = get_content_description(message)
            logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) sent {content_description} to {user_id[0]} via send all command')
            successful_sends += 1
        except telebot.apihelper.ApiException as e:
            logger.warning(f'Failed to send a message to user with user_id - {user_id}: {e}')
        total_users += 1
    bot_reply_content = content_description if message.content_type != 'text' else f'Сообщение:\n{message.text}'
    bot.reply_to(message, f'Сообщение отправлено {successful_sends} из {total_users} пользователей:\n{bot_reply_content}' if user_language == 'rus'
                else f'Повідомлення відправлене {successful_sends} з {total_users} користувачів:\n{bot_reply_content}')

@bot.message_handler(func=lambda message: message.text in ['Найти стикеры', 'Знайти стикери'], content_types=['text'])
def get_sticker_text_to_find_sticker(message):
    user_language = get_user_language(message.chat.id)

    msg = bot.reply_to(message, 'Введите текст для поиска стикеров' if user_language == 'rus' else 'Введіть текст для пошуку стикерів')
    logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) tried to find sticker')

    bot.register_next_step_handler(msg, find_stickers)

def find_stickers(message):
    with sqlite3.connect('stickers.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT sticker_id, keyword FROM stickers""")
        stickers = cursor.fetchall()

    user_language = get_user_language(message.chat.id)

    result = []
    for sticker in stickers:
        try:
            if message.text.lower() in sticker[1].lower():
                result.append(sticker[0])
        except AttributeError as e:
            logger.warning(f'User {message.from_user.username}(user_id - {message.from_user.id}) sent something that caused AttributeError: {e}')
            bot.send_sticker(message.chat.id, 'CAACAgIAAxUAAWT0z6Md0UVZkLHqaVvFesY_3q66AAJoIAAC4SO4SjsRfJMSVWi6MAQ')
            return

    if result:
        for sticker in result:
            sleep(0.5)
            bot.send_sticker(message.chat.id, sticker)
        logger.info(f'Sent {len(result)} stickers to user {message.from_user.username}(user_id - {message.from_user.id}). Searching text was {message.text}')
    else:
        bot.reply_to(message, 'Нет стикеров с таким текстом' if user_language == 'rus' else 'Нема стикерів з таким текстом')
        logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) did not find any sticker. Searching text was {message.text}')

@bot.message_handler(func=lambda message: message.text in ['Поменять язык', 'Змінити мову'], content_types=['text'])
def change_language(message):
    user_language = get_user_language(message.chat.id)
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    first_group = telebot.types.InlineKeyboardButton(text='Русский' if user_language == 'rus' else 'Російська', callback_data='rus')
    ukr_lang = telebot.types.InlineKeyboardButton(text="Украинский" if user_language == 'rus' else 'Українська', callback_data='ukr')

    keyboard.add(first_group, ukr_lang)

    bot.send_message(message.chat.id, 'На какой язык поменять?' if user_language == 'rus' else 'На яку мову змінити?', reply_markup=keyboard)
    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to change language')

@bot.callback_query_handler(func=lambda call: call.data == 'rus' or call.data == 'ukr')
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
        result = cursor.fetchone()
        if result:
            is_admin = result[0]
        else:
            is_admin = 0
        
        conn.commit()
        conn.close()
        
        bot.answer_callback_query(call.id, 'Язык изменён')
        
        keyboard = update_buttons('rus', is_admin, 'settings')

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
        result = cursor.fetchone()
        if result:
            is_admin = result[0]
        else:
            is_admin = 0
        
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, 'Мову змінено')
        
        keyboard = update_buttons('ukr', is_admin, 'settings')
        
        logger.info(f'User {call.message.chat.username}(user_id - {call.message.chat.id}) changed language to ukrainian')

        bot.send_message(chat_id=call.message.chat.id, text='Зараз обрана українська мова', reply_markup=keyboard)

    bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.message_id, reply_markup='')

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['change_group'])
def change_group(message):
    user_language = get_user_language(message.chat.id)
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    first_group = telebot.types.InlineKeyboardButton(text='ВД02-01', callback_data='1')
    second_group = telebot.types.InlineKeyboardButton(text='ВД02-02', callback_data='2')

    keyboard.add(first_group, second_group)

    bot.send_message(message.chat.id, 'В какой группе по социологии вы находитесь?' if user_language == 'rus' else 'В якій групі з соціології ви знаходитесь?', reply_markup=keyboard)
    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to change group')

@bot.callback_query_handler(func=lambda call: call.data == '1' or call.data == '2')
def answer_change_group(call):
    new_user_group_number = int(call.data)
    new_user_group = 'ВД02-01' if new_user_group_number == 1 else 'ВД02-02'

    user_language = get_user_language(call.message.chat.id)
    user_group = get_user_group(call.message.chat.id)

    if new_user_group_number == user_group:
        bot.answer_callback_query(call.id, 'Эта группа уже выбрана' if user_language == 'rus' else 'Ця група вже обрана')
        logger.info(f'User {call.message.chat.username} ({call.from_user.first_name})(user_id - {call.message.chat.id}) had been already in {new_user_group} group')
        return

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()

        cursor.execute("""UPDATE subscriptions SET user_group = ? WHERE user_id == ?""", (new_user_group_number, call.message.chat.id, ))
        conn.commit()

    bot.answer_callback_query(call.id, 'Группа изменена' if user_language == 'rus' else 'Групу змінено')
    logger.info(f'User {call.message.chat.username} ({call.from_user.first_name})(user_id - {call.message.chat.id}) changed group to {new_user_group}')
    bot.send_message(chat_id=call.message.chat.id, text=f'Сейчас выбрана группа {new_user_group}')

    bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.message_id, reply_markup='')

def start_bot_polling():
    RETRY_DELAY = 10
    while True:
        try:
            bot.polling(none_stop=True)
            break
        except (requests.exceptions.ReadTimeout, ApiTelegramException) as e:
            if isinstance(e, ApiTelegramException) and e.error_code == 502:
                print("Ошибка 502: Bad Gateway. Повторная попытка...")
            elif isinstance(e, requests.exceptions.ReadTimeout):
                print("Ошибка таймаута. Повторная попытка...")

            sleep(RETRY_DELAY)

if __name__ == '__main__':
    sc.every().monday.at('07:00').do(send_schedule)
    sc.every().tuesday.at('07:00').do(send_schedule)
    sc.every().wednesday.at('07:00').do(send_schedule)
    sc.every().thursday.at('07:00').do(send_schedule)
    sc.every().friday.at('07:00').do(send_schedule)

    thread = Thread(target=schedule_checker, daemon=True)
    thread.start()

    start_bot_polling()

    while thread.is_alive:
        thread.join(1)
