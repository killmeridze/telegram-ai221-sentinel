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

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT quote_tag FROM subscriptions WHERE user_id == ?""", (chat_id, ))
        fetched = cursor.fetchone()

    tag = fetched[0] if fetched is not None else 'Success'

    return tag

def escape_chars(text: str) -> str:
    '''Функция для экранирования символов в text'''
    chars_to_escape = ['|', '_', '-', '=', '.', '!']
    
    for char in chars_to_escape:
        text = text.replace(char, f"\{char}")

    return text

def get_platform(link: str) -> str:
    '''Функция для получения платформы по ссылке link'''
    if 'zoom' in link:
        return 'Zoom'
    elif 'meet.google' in link:
        return 'Google Meet'
    elif 'teams.microsoft' in link:
        return 'Microsoft Teams'


def quote_tags_by_letters() -> str:
    return """A: Age
B: Business 
C: Change, Character, Competition, Conservative, Courage, Creativity 
E: Education, Ethics 
F: Failure, Faith, Family, Famous Quotes, Film, Freedom, Friendship, Future
G: Generosity, Genius, Gratitude
H: Happiness, Health, History, Honor, Humorous
I: Imagination, Inspirational
K: Knowledge
L: Leadership, Life, Literature, Love
M: Mathematics, Motivational
N: Nature
O: Opportunity
P: Pain, Perseverance, Philosophy, Politics, Power Quotes
R: Religion
S: Sadness, Science, Self, Self Help, Social Justice, Society, Spirituality, Sports, Stupidity, Success
T: Technology, Time, Tolerance, Truth
V: Virtue
W: War, Weakness, Wellness, Wisdom, Work"""
