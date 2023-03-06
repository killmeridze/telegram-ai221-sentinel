# -*- coding: utf-8 -*-
import telebot
import datetime

bot = telebot.TeleBot('5844782786:AAGqpYHZMmRZ3sfWdoGioA8FODBweFEG-eA')

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text="Привет, сливка! Введи /schedule для того, чтобы получить расписание на сегодня.")

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(chat_id=message.chat.id, text="Список доступных команд:\n/schedule")

@bot.message_handler(commands=['schedule'])
def schedule(message):
    now = datetime.datetime.now()
    day = now.strftime("%A").lower()

    try:
        schedule = SCHEDULE[day]
    except KeyError:
        bot.send_message(chat_id=message.chat.id, text="Ты бессмертн(-ый/-ая) что ли? Иди проспись")
        return

    message_text = "Расписание на сегодня:\n\n"

    for item in schedule:
        message_text += "{}{}:\n".format(item['time'], item['name'])

        for link in item['links']:
            message_text += "{}\n".format(link)

    bot.send_message(chat_id=message.chat.id, text=message_text)

if __name__ == '__main__':
    SCHEDULE = {
        'monday': [
            {
                'time': '9:50-11:25\n',
                'name': 'Дискретная математика (Лекция)',
                'links': [
                    'https://zoom.us/j/4951329852?pwd=eEtLNmRCUnpiY2ZUNGdFK1JqSkJWdz09\n'
                ]
            },
            {
                'time': '11:40-13:15\n',
                'name': 'Операционные системы (Лекция)',
                'links': [
                    'https://us02web.zoom.us/j/87688751716?pwd=MnlJa2pXN1dGeUgwMUprdjJwODJzQT09'
                    '\n\nТерпения тебе!'
                ]
            },
        ],
        'tuesday': [
            {
                'time': '9:50-11:25\n',
                'name': 'Алгоритмизация н/п (Лаб)',
                'links': [
                    'https://zoom.us/j/98778795282?pwd=eEtLNmRCUnpiY2ZUNGdFK1JqSkJWdz09',
                    'Пароль:893295\n'
                ]
            },
            {
                'time': '9:50-11:25\n',
                'name': 'Алгоритмизация парная (Практ)',
                'links': [
                    'https://us02web.zoom.us/j/89424759693?pwd=eDFjMnJSL1lpVDFEdjVDSWhnRTdLZz09\n',
                ]
            },
            {
                'time': '11:40-13:15\n',
                'name': 'Дискретная математика (Практ)',
                'links': [
                    'https://zoom.us/j/4951329852?pwd=eEtLNmRCUnpiY2ZUNGdFK1JqSkJWdz09',
                    '\nТерпения тебе!'
                ]
            },
        ],
        'wednesday': [
            {
                'time': '8:00-9:35\n',
                'name': 'Английский язык (Практ)',
                'links': [
                    'https://us05web.zoom.us/j/5884802236?pwd=eDVCOVlLdHJ4ZmVDaVVQTFhtMml1Zz09'
                    '\nПароль:11111111\n'
                ]
            },
            {
                'time': '9:50-11:25\n',
                'name': 'Выш.мат (Лекция)',
                'links': [
                    'https://us05web.zoom.us/j/6640162782?pwd=eDVCOVlLdHJ4ZmVDaVVQTFhtMml1Zz09'
                    '\nПароль:8NWy4H\n'
                ]
            },
            {
                'time': '11:40-13:15\n',
                'name': 'Прикладная физика (Лекция)',
                'links': [
                    '*нет ссылки*'
                    '\n\nТерпения тебе! (Особенно с Усовым)'
                ]
            }
        ],
        'thursday': [
            {
                'time': '9:50-11:25\n',
                'name': 'Выш.мат (Практ)',
                'links': [
                    'https://us05web.zoom.us/j/88252951933?pwd=MlZUdllYWE8rN3RVMTV5SmpjT2V6QT09\n'
                ]
            },
            {
                'time': '11:40-13:15\n',
                'name': 'Операционные системы (Лаб)',
                'links': [
                    'https://us02web.zoom.us/j/87688751716?pwd=MnlJa2pXN1dGeUgwMUprdjJwODJzQT09\n'
                    '\nТерпения тебе! (Слава богу Желиба)'
                ]
            }
        ],
        'friday': [
            {
                'time': '9:50-11:25\n',
                'name': 'Алгоритмизация (Лекция)',
                'links': [
                    'https://us02web.zoom.us/j/89424759693?pwd=eDFjMnJSL1lpVDFEdjVDSWhnRTdLZz09\n'
                ]
            },
            {
                'time': '11:40-13:15\n',
                'name': 'Прикладная физика (Лаб)',
                'links': [
                    '*нет ссылки*\n'
                    '\nТерпения тебе!'
                ]
            }
        ]
    }
bot.polling(none_stop=True)
