# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler
import datetime

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет, сливка! Введи /schedule для того, чтобы получить расписание на сегодня.")

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Список доступных команд:\n/schedule")

def schedule(update, context):
    now = datetime.datetime.now()
    day = now.strftime("%A").lower()

    try:
        schedule = SCHEDULE[day]
    except KeyError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Ты бессмертн(-ый/-ая) что ли? Иди проспись")
        return

    message = "Расписание на сегодня:\n\n"

    for item in schedule:
        message += "{}{}:\n".format(item['time'], item['name'])

        for link in item['links']:
            message += "{}\n".format(link)

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

if __name__ == '__main__':
    bot_token = '5844782786:AAGqpYHZMmRZ3sfWdoGioA8FODBweFEG-eA'

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
    updater = Updater(token=bot_token, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('schedule', schedule))

    updater.start_polling()
    updater.idle()
