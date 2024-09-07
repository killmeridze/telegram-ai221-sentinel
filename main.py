from telebot.apihelper import ApiTelegramException
from dotenv import load_dotenv
from threading import Thread
from telebot import types
from loguru import logger
from time import sleep
import schedule as sc
from utils import *
import datetime
import settings
import requests
import telebot
import sqlite3
import quotes
import json
import os

logger.add('logging.log', format='{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}', level='DEBUG', rotation='10 MB', compression='zip')

load_dotenv()

TOKEN = os.getenv('TOKEN')
ADMINS = [int(admin) for admin in os.getenv('ADMINS').split(',')]
with open('button_texts.json', 'r', encoding='utf-8') as file:
    BUTTON_TEXTS = json.load(file)

bot = telebot.TeleBot(TOKEN)

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

    if day_name_en != 'saturday':
        # Проверка на чётность/нечётность. False - нечётная, True - чётная
        current_week_number = today.isocalendar()[1]
        week_parity = (current_week_number - settings.FIRST_WEEK_NUMBER) % 2 != 0
    else:
        schedule_day = schedule[0].get('schedule-day', 0)

        day = schedule_day % 5 + 1
        week_parity = ((schedule_day // 5) + 1) % 2 == 0

        with open(schedule_file, 'r', encoding='utf-8') as file:
            schedule = json.load(file).get(settings.day_names[day])

    for item in schedule:
        if (item.get("week_parity") is None or item.get("week_parity") is week_parity) and (item.get("group") is None or item.get("group") is group):
            message_text += f'{item["time"]}\n{item["name"]}:\n'
            for link in item["links"]:
                if 'Пароль' in link:
                    message_text += f'{link}\n'
                else:
                    link_shortcut = 'Ссылка на ' if language == 'rus' else 'Посилання на '
                    link_shortcut += get_platform(link)
                    message_text += f'[{link_shortcut}]({link})\n'
            message_text += f'{item["teachers"]}\n\n'

    return message_text

def send_schedule() -> None:
    '''Функция для авторассылки сообщений'''

    today = datetime.date.today()

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT user_id, language, user_group, quotes_subscribed FROM subscriptions WHERE subscribed == 1""")
        subscribers = cursor.fetchall()

    for subscriber in subscribers:
        try:
            message_text = schedule_text(today, subscriber[1], subscriber[2])

            if subscriber[3]:
                message_text += f"\n>{quotes.get_random_quote(get_user_quote_tag(subscriber[0]), subscriber[1][:-1])}**"
            
            message_text = escape_chars(message_text)

            bot.send_message(chat_id=subscriber[0], text=message_text, parse_mode="MarkdownV2", link_preview_options=types.LinkPreviewOptions(is_disabled=True))
            logger.info(f'Sent schedule to user_id - {subscriber[0]} via autosending')
        except telebot.apihelper.ApiException as e:
            logger.warning(f'Failed to send a schedule to user with user_id - {subscriber[0]}: {e}')
            sleep(1)

    if today.strftime("%A").lower() == 'tuesday':
        schedule_files = ['rus_schedule.json', 'ukr_schedule.json']
        for schedule_file in schedule_files:
            with open(schedule_file, 'r', encoding='utf-8') as file:
                data = json.load(file)

            data['saturday'][0]['schedule-day'] += 1

            with open(schedule_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

def update_buttons(language: str, user_id: int, is_admin: bool = False, mode: str = 'main') -> types.ReplyKeyboardMarkup:
    '''Функция для обновления кнопок в соответствии с языком пользователя и выбранным режимом.'''

    # Главное меню
    if mode == 'main':
        button = types.KeyboardButton(BUTTON_TEXTS[language]["schedule"])
        button_tomorrow = types.KeyboardButton(BUTTON_TEXTS[language]["schedule_tomorrow"])
        button_subscribe_unsubscribe = get_subcribe_unsubscibe_button(language, user_id)
        button_find_sticker = types.KeyboardButton(BUTTON_TEXTS[language]["find_sticker"])
        button_settings = types.KeyboardButton(BUTTON_TEXTS[language]["settings"])
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(button, button_tomorrow)
        keyboard.row(button_subscribe_unsubscribe)
        keyboard.row(button_find_sticker, button_settings)

        if is_admin:
            button_send_all = types.KeyboardButton(BUTTON_TEXTS[language]["send_all"])
            keyboard.row(button_send_all)
    
    # Меню настроек
    elif mode == 'settings':
        button_change_language = types.KeyboardButton(BUTTON_TEXTS[language]["change_language"])
        button_change_group = types.KeyboardButton(BUTTON_TEXTS[language]["change_group"])
        button_configure_quote = types.KeyboardButton(BUTTON_TEXTS[language]["configure_quote"])
        button_return = types.KeyboardButton(BUTTON_TEXTS[language]["return"])

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(button_change_language, button_change_group)
        keyboard.row(button_configure_quote)
        keyboard.row(button_return)

    # Меню цитат
    elif mode == 'quotes':
        subscribe_quote_button = get_subcribe_unsubscibe_quote_button(language, user_id)
        change_quote_theme_button = types.KeyboardButton(BUTTON_TEXTS[language]["change_quote_theme"])
        return_to_settings_button = types.KeyboardButton(BUTTON_TEXTS[language]["return_to_settings"])

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(subscribe_quote_button,change_quote_theme_button)
        keyboard.row(return_to_settings_button)

    return keyboard

def get_subcribe_unsubscibe_button(language: str, user_id: int) -> types.KeyboardButton:
    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT subscribed FROM subscriptions WHERE user_id == ?""", (user_id, ))
        fetched = cursor.fetchone()
        subscribed = fetched[0] if fetched else False

    return types.KeyboardButton(BUTTON_TEXTS[language]["unsubscribe"] if subscribed else BUTTON_TEXTS[language]["subscribe"])

def get_subcribe_unsubscibe_quote_button(language: str, user_id: int) -> types.KeyboardButton:
    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT quotes_subscribed FROM subscriptions WHERE user_id == ?""", (user_id, ))
        fetched = cursor.fetchone()
        quotes_subscribed = fetched[0] if fetched else False

    return types.KeyboardButton(BUTTON_TEXTS[language]["unsubscribe_quotes"] if quotes_subscribed else BUTTON_TEXTS[language]["subscribe_quotes"])

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['settings'])
def show_settings(message: types.Message) -> None:
    user_language = get_user_language(message.chat.id)
    prompt_text = 'Выберите действие:' if user_language == 'rus' else 'Оберіть дію:'
    bot.send_message(message.chat.id, prompt_text, reply_markup=update_buttons(user_language, message.chat.id, mode='settings'))

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['return'])
def return_to_main(message: types.Message) -> None:
    user_language = get_user_language(message.chat.id)

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT is_admin FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
        is_admin = cursor.fetchone()[0]

    prompt_text = 'Что делать дальше? Выбор за тобой, сливка' if user_language == 'rus' else 'Що робити далi? Вибiр за тобою, слiвка'
    bot.send_message(message.chat.id, prompt_text, reply_markup=update_buttons(user_language, message.chat.id, is_admin, mode='main'))

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]["return_to_settings"])
def return_to_settings(message: types.Message) -> None:
    user_language = get_user_language(message.chat.id)
    prompt_text = 'Что делать дальше? Выбор за тобой, сливка' if user_language == 'rus' else 'Що робити далi? Вибiр за тобою, слiвка'
    bot.send_message(message.chat.id, prompt_text, reply_markup=update_buttons(user_language, message.chat.id, mode='settings'))

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]["configure_quote"])
def handle_configure_quote(message: types.Message) -> None:
    user_language = get_user_language(message.chat.id)
    prompt_text = 'Выберите опцию:' if user_language == 'rus' else 'Виберіть опцію:'
    bot.send_message(message.chat.id, prompt_text, reply_markup=update_buttons(user_language, message.chat.id, mode='quotes'))

@bot.message_handler(commands=['start'])
def start(message: types.Message) -> None:
    logger.info(f'New user - {message.from_user.username} ({message.from_user.first_name})')

    username = message.chat.username
    user_id = message.chat.id
    subscribed = 0
    language = 'rus'
    is_admin = 0

    if user_id in ADMINS:
        is_admin = 1

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS subscriptions
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        user_id INTEGER NOT NULL,
                        subscribed INTEGER NOT NULL CHECK (subscribed IN (0, 1)),
                        language TEXT NOT NULL CHECK (language IN ('rus', 'ukr')),
                        is_admin INTEGER NOT NULL CHECK (is_admin IN (0, 1)),
                        user_group INTEGER DEFAULT 1 CHECK (user_group IN (1, 2)),
                        quotes_subscribed INTEGER DEFAULT 0 CHECK (quotes_subscribed IN (0, 1)),
                        quote_tag TEXT DEFAULT 'Success')""")
        
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

    keyboard = update_buttons(language, is_admin)

    bot.send_message(chat_id=message.chat.id, text=BUTTON_TEXTS[language]["welcome_message"], reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['schedule'])
def schedule(message: types.Message) -> None:
    today = datetime.date.today()
    user_language = get_user_language(message.chat.id)
    user_group = get_user_group(message.chat.id)

    message_text = schedule_text(today, user_language, user_group)

    message_text = escape_chars(message_text)

    bot.send_message(chat_id=message.chat.id, text=message_text, parse_mode="MarkdownV2", link_preview_options=types.LinkPreviewOptions(is_disabled=True))
    logger.info(f'Sent schedule to {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) via command "{message.text}"')

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['schedule_tomorrow'])
def schedule_tomorrow(message: types.Message) -> None:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    user_language = get_user_language(message.chat.id)
    user_group = get_user_group(message.chat.id)
    message_text = schedule_text(tomorrow, user_language, user_group)

    message_text = escape_chars(message_text)

    bot.send_message(chat_id=message.chat.id, text=message_text, parse_mode="MarkdownV2", link_preview_options=types.LinkPreviewOptions(is_disabled=True))
    logger.info(f'Sent schedule to {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) via command "{message.text}"')

@bot.message_handler(func=lambda message: message.text in [BUTTON_TEXTS[get_user_language(message.chat.id)]['subscribe'], BUTTON_TEXTS[get_user_language(message.chat.id)]['unsubscribe']])
def subscribe_unsubscribe_handler(message: types.Message) -> None:
    user_language = get_user_language(message.chat.id)
    user_id = message.chat.id

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT subscribed, is_admin FROM subscriptions WHERE user_id == ?""", (user_id, ))
        fetched = cursor.fetchone()
        is_admin = fetched[1] if fetched else False
    
    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to subscribe/unsubscribe')
    if fetched is None or not fetched[0]:
        if fetched is None:
            update_query = """INSERT INTO subscriptions (user_id, subscribed) VALUES (?, 1)"""
        else:
            update_query = """UPDATE subscriptions SET subscribed = 1 WHERE user_id == ?"""
        success_message = 'Вы успешно подписались на рассылку!' if user_language == 'rus' else 'Ви успішно підписалися на розсилку!'
        logger.info(f"User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has successfully subscribed")
    else:
        update_query = """UPDATE subscriptions SET subscribed = 0 WHERE user_id == ?"""
        success_message = 'Вы успешно отписались от рассылки!' if user_language == 'rus' else 'Ви успішно відписалися від розсилки!'
        logger.info(f"User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has successfully unsubscribed")

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute(update_query, (user_id, ))
        conn.commit()

    bot.send_message(user_id, success_message, reply_markup=update_buttons(user_language, user_id, is_admin, mode='main'))

@bot.message_handler(func=lambda message: message.text in [BUTTON_TEXTS[get_user_language(message.chat.id)]['subscribe_quotes'], BUTTON_TEXTS[get_user_language(message.chat.id)]['unsubscribe_quotes']])
def handle_quotes_subscription(message: types.Message) -> None:
    user_language = get_user_language(message.chat.id)
    user_id = message.chat.id

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT quotes_subscribed FROM subscriptions WHERE user_id == ?""", (user_id, ))
        fetched = cursor.fetchone()

    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to subscribe/unsubscribe to/from quotes')
    if fetched is None or not fetched[0]:
        update_query = """UPDATE subscriptions SET quotes_subscribed = 1 WHERE user_id == ?"""
        success_message = 'Вы успешно подписались на цитаты!' if user_language == 'rus' else 'Ви успішно підписалися на цитати!'
        logger.info(f"User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has successfully subscribed to quotes")
    else:
        update_query = """UPDATE subscriptions SET quotes_subscribed = 0 WHERE user_id == ?"""
        success_message = 'Вы успешно отписались от цитат!' if user_language == 'rus' else 'Ви успішно відписалися від цитат!'
        logger.info(f"User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has successfully unsubscribed from quotes")

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute(update_query, (user_id, ))
        conn.commit()
    
    bot.send_message(user_id, success_message, reply_markup=update_buttons(user_language, user_id, mode='quotes'))

def get_content_description(message : types.Message) -> str:
    match message.content_type:
        case 'text':
            return f'text "{message.text}"'
        case 'photo':
            return 'a photo'
        case 'sticker':
            return 'a sticker'
        case 'animation':
            return 'an animation'
        case 'voice':
            return 'a voice'
        case _:
            return 'an unknown content'

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['send_all'], content_types=['text', 'photo', 'sticker', 'animation', 'voice'])
def get_text_to_send_all(message : types.Message) -> None:
    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT is_admin, language FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
        user_is_admin, user_language = cursor.fetchone()

    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to send all')
    if not user_is_admin:
        bot.reply_to(message, 'У вас нет прав на это' if user_language == 'rus' else 'У вас нема прав для цього')
        logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) has no rights to send all')
        return
    
    msg = bot.reply_to(message, 'Что вы хотите отправить всем?' if user_language == 'rus' else 'Що ви хочете відправити усім?')

    bot.register_next_step_handler(msg, send_all)

def send_all(message: types.Message) -> None:
    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT language FROM subscriptions WHERE user_id == ?""", (message.chat.id, ))
        user_language = cursor.fetchone()[0]

        cursor.execute("""SELECT user_id FROM subscriptions""")
        users_ids = cursor.fetchall()

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
            if e.error_code == 403 and 'bot was blocked by the user' in e.result.text:
                cursor.execute("""DELETE FROM subscriptions WHERE user_id = ?""", (user_id[0],))
                conn.commit()
                logger.info(f'User with user_id - {user_id[0]} has been removed from the database due to blocking the bot.')
            else:
                logger.warning(f'Failed to send a message to user with user_id - {user_id[0]}: {e}')
        total_users += 1
        sleep(1)
    
    bot_reply_content = content_description if message.content_type != 'text' else f'Сообщение:\n{message.text}'
    bot.reply_to(message, f'Сообщение отправлено {successful_sends} из {total_users} пользователей:\n{bot_reply_content}' if user_language == 'rus'
                else f'Повідомлення відправлене {successful_sends} з {total_users} користувачів:\n{bot_reply_content}')

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['find_sticker'])
def get_text_to_find_stickers(message : types.Message) -> None:
    user_language = get_user_language(message.chat.id)

    msg = bot.reply_to(message, 'Введите текст для поиска стикеров' if user_language == 'rus' else 'Введіть текст для пошуку стикерів')
    logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) tried to find sticker')

    bot.register_next_step_handler(msg, find_stickers)

def find_stickers(message : types.Message) -> None:
    user_language = get_user_language(message.chat.id)

    with sqlite3.connect('stickers.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT sticker_id, keyword FROM stickers""")
        stickers = cursor.fetchall()

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

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['change_quote_theme'])
def get_quote_tag_from_user(message : types.Message) -> None:
    user_language = get_user_language(message.chat.id)

    msg = bot.reply_to(message, ('Введите тему цитаты из списка ниже:\n' if user_language == 'rus' else 'Введіть тему цитати зі списку нижче:\n') + quote_tags_by_letters())
    logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) tried to change quote tag')

    bot.register_next_step_handler(msg, proccess_tag)

def proccess_tag(message : types.Message) -> None:
    user_language = get_user_language(message.chat.id)
    tag = message.text

    if tag not in settings.quote_tags:
        bot.reply_to(message, 'Такой темы нет в списке' if user_language == 'rus' else 'Такої теми немає у списку')
        logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) entered wrong tag - {tag}')
        return
    
    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""UPDATE subscriptions SET quote_tag = ? WHERE user_id = ?""", (tag, message.chat.id, ))
        conn.commit()

    bot.reply_to(message, 'Тема цитат изменена' if user_language == 'rus' else 'Тему цитат змінено')
    logger.info(f'User {message.from_user.username}(user_id - {message.from_user.id}) changed quote tag to {tag}')

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['change_language'])
def change_language(message : types.Message) -> None:
    user_language = get_user_language(message.chat.id)
    
    keyboard = types.InlineKeyboardMarkup()
    
    rus_lang = types.InlineKeyboardButton(text='Русский', callback_data='rus')
    ukr_lang = types.InlineKeyboardButton(text='Українська', callback_data='ukr')

    keyboard.add(rus_lang, ukr_lang)

    bot.send_message(message.chat.id, 'На какой язык поменять?' if user_language == 'rus' else 'На яку мову змінити?', reply_markup=keyboard)
    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to change language')

@bot.callback_query_handler(func=lambda call: call.data == 'rus' or call.data == 'ukr')
def answer_change_language(call : types.CallbackQuery) -> None:
    user_language = get_user_language(call.message.chat.id)
    full_language_name = 'russian' if call.data == 'rus' else 'ukranian'

    if user_language == call.data:
        bot.answer_callback_query(call.id, 'Этот язык уже выбран' if user_language == 'rus' else 'Ця мова вже обрана')
        logger.info(f'User {call.message.chat.username} ({call.from_user.first_name})(user_id - {call.message.chat.id}) already has {full_language_name} language')
        return
    
    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()

        cursor.execute("""UPDATE subscriptions SET language = ? WHERE user_id == ?""", (call.data, call.message.chat.id))
        conn.commit()
        
        cursor.execute("""SELECT is_admin FROM subscriptions WHERE user_id == ?""", (call.message.chat.id, ))
        is_admin = cursor.fetchone()[0] 

    bot.answer_callback_query(call.id, 'Язык изменён' if call.data == 'rus' else 'Мову змінено')
    
    keyboard = update_buttons(call.data, is_admin, 'settings')

    logger.info(f'User {call.message.chat.username} ({call.from_user.first_name})(user_id - {call.message.chat.id}) changed language to {full_language_name}')

    bot.send_message(chat_id=call.message.chat.id, text='Сейчас выбран русский язык' if call.data == 'rus' else 'Зараз обрана українська мова', reply_markup=keyboard)
    bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.message_id, reply_markup='')

@bot.message_handler(func=lambda message: message.text == BUTTON_TEXTS[get_user_language(message.chat.id)]['change_group'])
def change_group(message : types.Message) -> None:
    user_language = get_user_language(message.chat.id)
    
    keyboard = types.InlineKeyboardMarkup()
    
    first_group = types.InlineKeyboardButton(text='ВД01-14', callback_data='1')
    second_group = types.InlineKeyboardButton(text='ВД01-15', callback_data='2')

    keyboard.add(first_group, second_group)

    bot.send_message(message.chat.id, 'В какой группе по психологии вы находитесь?' if user_language == 'rus' else 'В якій групі з психологоії ви знаходитесь?', reply_markup=keyboard)
    logger.info(f'User {message.from_user.username} ({message.from_user.first_name})(user_id - {message.from_user.id}) tried to change group')

@bot.callback_query_handler(func=lambda call: call.data == '1' or call.data == '2')
def answer_change_group(call : types.CallbackQuery) -> None:
    new_user_group_number = int(call.data)
    new_user_group = 'ВД01-14' if new_user_group_number == 1 else 'ВД01-15'

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
    bot.send_message(chat_id=call.message.chat.id, text=f'Сейчас выбрана группа {new_user_group}' if user_language == 'rus' else f'Зараз обрана група {new_user_group}')

    bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.message_id, reply_markup='')

def start_bot_polling() -> None:
    RETRY_DELAY_BASE = 2  # Начальная задержка
    MAX_RETRY_DELAY = 600  # Максимальная задержка в секундах (10 минут)
    
    retry_delay = RETRY_DELAY_BASE  # Начальное значение задержки
    
    while True:
        try:
            bot.polling(none_stop=True)
            break
        except (requests.exceptions.ReadTimeout, ApiTelegramException, requests.exceptions.ConnectionError) as e:
            if isinstance(e, ApiTelegramException) and e.error_code == 502:
                error_message = "Ошибка 502: Bad Gateway. Повторная попытка..."
            elif isinstance(e, requests.exceptions.ReadTimeout):
                error_message = "Ошибка таймаута. Повторная попытка..."
            elif isinstance(e, requests.exceptions.ConnectionError):
                error_message = "Ошибка соединения. Повторная попытка..."

            print(error_message)

            sleep(retry_delay)
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)

def schedule_checker() -> None:
    while True:
        sc.run_pending()
        sleep(1)

if __name__ == '__main__':
    sc.every().monday.at('07:00').do(send_schedule)
    sc.every().tuesday.at('07:00').do(send_schedule)
    sc.every().wednesday.at('07:00').do(send_schedule)
    sc.every().thursday.at('07:00').do(send_schedule)
    sc.every().friday.at('07:00').do(send_schedule)
    sc.every().saturday.at('07:00').do(send_schedule)
    # sc.every().second.do(send_schedule)

    thread = Thread(target=schedule_checker, daemon=True)
    thread.start()

    start_bot_polling()

    while thread.is_alive:
        thread.join(1)
