import datetime



FIRST_WEEK_NUMBER = 10

#Узнаём номер недели
today = datetime.date.today()
current_week_number = today.isocalendar()[1]

#Проверка на чётность/нечётность
week_parity = False
if (current_week_number - FIRST_WEEK_NUMBER) % 2 == 0:
    week_parity = False
else:
    week_parity = True
