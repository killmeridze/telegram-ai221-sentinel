# -*- coding: utf-8 -*-
import telebot
from telebot import types
import datetime
import json

bot = telebot.TeleBot('5844782786:AAGqpYHZMmRZ3sfWdoGioA8FODBweFEG-eA')

@bot.message_handler(commands=['start'])
def start(message):
    button = telebot.types.KeyboardButton('/Расписание')
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(button)
    bot.send_message(chat_id=message.chat.id, text='Привет, сливка! Нажми на кнопку, чтобы получить расписание!', reply_markup=keyboard)

@bot.message_handler(commands=['Расписание'])
def schedule(message):
    now = datetime.datetime.now()
    day = now.strftime('%A').lower()

    with open('day_names_ru.json', 'r', encoding='utf-8') as f:
        day_names = json.load(f)

    day_ru = day_names.get(day, day)

    with open('schedule.json', 'r', encoding='utf-8') as f:
        schedule = json.load(f).get(day)

    if not schedule:
        bot.send_message(chat_id=message.chat.id, text='Ты бессмертн(-ый/-ая) что ли? Иди проспись')
        return

    message_text = f"Расписание на {day_ru.capitalize()}:\n\n"

    for item in schedule:
        message_text += '{}{}:\n'.format(item['time'], item['name'])

        for link in item['links']:
            message_text += '{}\n'.format(link)

    bot.send_message(chat_id=message.chat.id, text=message_text)

if __name__ == '__main__':   
    bot.polling(none_stop=True)
