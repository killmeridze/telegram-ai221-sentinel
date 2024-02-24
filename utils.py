import sqlite3

def get_user_language(chat_id: int) -> str:
    '''Функция для получения языка пользователя'''

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT language FROM subscriptions WHERE user_id == ?""", (chat_id, ))
        fetched = cursor.fetchone()
    
    language = fetched[0] if fetched is not None else "rus"

    return language

def get_user_group(chat_id: int) -> str:
    '''Функция для получения группы пользователя'''

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT user_group FROM subscriptions WHERE user_id == ?""", (chat_id, ))
        fetched = cursor.fetchone()

    group = fetched[0] if fetched is not None else 1

    return group

def get_user_quote_tag(chat_id: int) -> str:
    '''Функция для получения тэга цитаты пользователя'''
    return "Inspirational" # Заглушка пока

def escape_chars(text: str) -> str:
    '''Функция для экранирования символов в text'''
    chars_to_escape = ['|', '_', '(', ')', '-', '=', '.', '!']
    
    for char in chars_to_escape:
        text = text.replace(char, f"\{char}")

    return text