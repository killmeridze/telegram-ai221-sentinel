import sqlite3

chars = ['_', '(', ')', '-', '=', '.', '!']

def get_user_language(chat_id: int) -> str:
    '''Функция для получения языка пользователя'''

    with sqlite3.connect('subscriptions.db') as conn:
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

def escape_chars(chars: list[str], text: str) -> str:
    for char in chars:
        text = text.replace(char, f"\{char}")

    return text