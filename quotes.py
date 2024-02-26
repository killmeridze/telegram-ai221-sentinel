from loguru import logger
import requests
import settings

logger.add('logging.log', format='{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}', level='DEBUG', rotation='10 MB', compression='zip')

quotes_api_url = "https://api.quotable.io"
translation_api_url = "https://api.mymemory.translated.net"

def get_random_quote(tag: str, lang: str) -> str | None:
    '''Функция для получения случайной цитаты по tag'у и на языкe lang'''

    if (tag not in settings.quote_tags):
        logger.warning(f"Tag list doesn't contain {tag}")
        return
    
    response = requests.get(f"{quotes_api_url}/quotes/random?tags={tag}")

    if response.ok:
        text = response.json()[0]["content"]
        author = response.json()[0]["author"]

        translation_response = requests.get(f"{translation_api_url}/get?q={text} © {author}&langpair=en|{lang}")

        if (translation_response.ok):
            quote = translation_response.json()["responseData"]["translatedText"]
        else:
            logger.error(f"Translation API Error: {translation_response.status_code}")
            return f'{text} © {author}'
    else:
        logger.error(f"Quotes API Error: {response.status_code}")
        return

    return quote