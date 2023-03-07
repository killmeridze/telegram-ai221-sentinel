import telebot
import datetime
import json
import settings



bot = telebot.TeleBot('5844782786:AAGqpYHZMmRZ3sfWdoGioA8FODBweFEG-eA')

@bot.message_handler(commands=['start'])
def start(message):
    button = telebot.types.KeyboardButton('/Расписание')
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(button)
    bot.send_message(chat_id=message.chat.id, text='Привет, сливка! Нажми на кнопку, чтобы получить расписание!', reply_markup=keyboard)

@bot.message_handler(commands=['Расписание'])
def schedule(message):
    today = datetime.date.today()

    #Проверка на чётность/нечётность False - нечётная, True - чётная
    current_week_number = today.isocalendar()[1]
    week_parity = False
    if (current_week_number - settings.FIRST_WEEK_NUMBER) % 2 == 0:
        week_parity = False
    else:
        week_parity = True
    
    day_name_en = today.strftime('%A').lower()
    day_name_ru = settings.weekday_name_ru_dict.get(day_name_en, day_name_en)

    with open('schedule.json', 'r', encoding='utf-8') as f:
        schedule = json.load(f).get(day_name_en)

    if not schedule:
        bot.send_message(chat_id=message.chat.id, text="Ты бессмертн(-ый/-ая) что ли? Иди проспись")
        return

    message_text = f"Расписание на {day_name_ru}:\n\n"

    for item in schedule:
        if item.get('week_parity') is None:
            message_text += f"{item['time']}{item['name']}:\n"
            for link in item["links"]:
                message_text += f"{link}\n"

        elif item.get('week_parity') is week_parity:
            message_text += f"{item['time']}{item['name']}:\n"
            for link in item["links"]:
                message_text += f"{link}\n"

    bot.send_message(chat_id=message.chat.id, text=message_text)

if __name__ == '__main__':   
    bot.polling(none_stop=True)
