# -*- coding: utf-8 -*-
import telebot
import datetime
import json

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

    with open("schedule.json", "r", encoding="utf-8") as f:
        schedule = json.load(f).get(day)

    if not schedule:
        bot.send_message(chat_id=message.chat.id, text="Ты бессмертн(-ый/-ая) что ли? Иди проспись")
        return

    message_text = "Расписание на сегодня:\n\n"

    for item in schedule:
        message_text += "{}{}:\n".format(item['time'], item['name'])

        for link in item['links']:
            message_text += "{}\n".format(link)

    bot.send_message(chat_id=message.chat.id, text=message_text)

if __name__ == '__main__':   
    bot.polling(none_stop=True)
