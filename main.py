import csv
import sqlite3
import schedule

import telebot
from telebot import types
from datetime import date, timedelta, datetime

import config

bot = telebot.TeleBot(config.token, parse_mode='HTML')
current_name = ''
chosen_direction = ''
possible_dates = []
selected_date = ''
consultation_start = ''
consultation_duration = ''
selected_specialist = ''
selected_time_begin_end = []
weekend_specialist_name = ''
weekend_date = ''


@bot.message_handler(commands=['Выходной'])
def add_weekend(message):
    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()

    cur.execute('SELECT name FROM specialists')
    names_specialists = cur.fetchall()
    display_names_specialists_str = 'Имена специалистов в базе:\n'
    for i in names_specialists:
        k = i[0]
        display_names_specialists_str += k + '\n'
    display_names_specialists_str += 'Введите ваше имя'
    bot.send_message(message.chat.id, display_names_specialists_str)
    conn.commit()
    cur.close()
    conn.close()
    bot.register_next_step_handler(message, choose_date)


def choose_date(message):
    global weekend_specialist_name
    weekend_specialist_name = message.text
    bot.send_message(message.chat.id, 'Введите дату в формате (гггг-мм-дд)')
    bot.register_next_step_handler(message, weekend_confirmation)


def weekend_confirmation(message):
    global weekend_date, weekend_specialist_name
    weekend_date = message.text
    markup = types.ReplyKeyboardMarkup()
    btnY = types.KeyboardButton('Да')
    btnN = types.KeyboardButton("Нет")
    markup.add(btnY, btnN)
    bot.send_message(message.chat.id, "Выходной:\nСпециалист:%s\nДата:%s" % (weekend_specialist_name, weekend_date),
                     reply_markup=markup)
    bot.register_next_step_handler(message, weekend_YN)


def weekend_YN(message):
    if message.text == 'Да':
        global weekend_date, weekend_specialist_name
        conn = sqlite3.connect('arkana_data_base.sql')
        cur = conn.cursor()
        cur.execute("INSERT INTO consultations (date_consultation, time_begin, time_end, specialist_name) "
                    "VALUES ('%s', '11:00', '21:00', '%s')" % (weekend_date, weekend_specialist_name))
        print("INSERT INTO consultations (date_consultation, time_begin, time_end, specialist_name) "
              "VALUES ('%s', '11:00', '21:00', '%s')" % (weekend_date, weekend_specialist_name))
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(message.chat.id, 'Выходной добавлен')
    else:
        add_weekend(message)


@bot.message_handler(commands=['Список_клиентов'])
def display_list_users(message):
    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    with open("Список клиентов.csv", "w", newline='') as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(["Список клиентов:"])
        writer.writerow(["Имя клиента"])

    for i in users:
        with open("Список клиентов.csv", "a", newline='') as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow([i[1]])
    bot.send_document(message.chat.id, document=open("Список клиентов.csv", "rb"))


@bot.message_handler(commands=['Список_консультаций'])
def display_consultations(message):
    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM consultations')
    consultation = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    with open("Список консультаций.csv", "w", newline='', encoding="cp1251") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Список клиентов"])
        writer.writerow(["Порядковый номер", "Дата", "Время начала", "Время конца", "Имя клиента", "Специалист"])

    for i in consultation:
        with open("Список консультаций.csv", "a", newline='', encoding="cp1251") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(i)
    bot.send_document(message.chat.id, document=open("Список консультаций.csv", "rb"))


@bot.message_handler(commands=['create_data_base'])
def create_data_base(message):
    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name nchar(100))')
    cur.execute('CREATE TABLE IF NOT EXISTS directions (id int auto_increment primary key, name_direction nchar(100))')
    cur.execute('CREATE TABLE IF NOT EXISTS specialists (id int auto_increment primary key, name nchar(100), '
                'direction nchar(100) REFERENCES direction(name_direction))')
    cur.execute('CREATE TABLE IF NOT EXISTS consultations (id int auto_increment primary key, date_consultation date, '
                'time_begin time, time_end time, user_name nchar(100) REFERENCES users(name), specialist_name '
                'nchar(100) REFERENCES specialists(name))')
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, "база данных создана")


@bot.message_handler(commands=['filling_with_test_data'])
def filling_with_test_data(message):
    current_date = (date.today())
    week_date = []
    for i in range(4):
        week_date.append(str(current_date + timedelta(days=i)))

    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()

    cur.execute("INSERT INTO users (name) VALUES ('Иванов Иван Иванович 1')")
    cur.execute("INSERT INTO users (name) VALUES ('Иванов Иван Иванович 2')")
    cur.execute("INSERT INTO users (name) VALUES ('Иванов Иван Иванович 3')")
    cur.execute("INSERT INTO users (name) VALUES ('Иванов Иван Иванович 4')")

    cur.execute("INSERT INTO directions (name_direction) VALUES ('Семейная консультация')")
    cur.execute("INSERT INTO directions (name_direction) VALUES ('Подростковая консультация')")
    cur.execute("INSERT INTO directions (name_direction) VALUES ('Индивидуальная консультация')")
    cur.execute("INSERT INTO directions (name_direction) VALUES ('Детская консультация')")

    cur.execute("INSERT INTO specialists (name, direction) VALUES ('Петр Петрович Петров 1', 'Семейная консультация')")
    cur.execute(
        "INSERT INTO specialists (name, direction) VALUES ('Петр Петрович Петров 2', 'Подростковая консультация')")
    cur.execute(
        "INSERT INTO specialists (name, direction) VALUES ('Петр Петрович Петров 3', 'Индивидуальная консультация')")
    cur.execute(
        "INSERT INTO specialists (name, direction) VALUES ('Петр Петрович Петров 4', 'Индивидуальная консультация')")
    cur.execute("INSERT INTO specialists (name, direction) VALUES ('Петр Петрович Петров 5', 'Детская консультация')")
    cur.execute(
        "INSERT INTO specialists (name, direction) VALUES ('Петр Петрович Петров 6', 'Подростковая консультация')")

    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '11:30', '11:45', 'Иванов Иван Иванович 2', 'Петр Петрович Петров 5')" % (
            week_date[0]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '13:00', '13:45', 'Иванов Иван Иванович 1', 'Петр Петрович Петров 4')" % (
            week_date[0]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '11:00', '11:45', 'Иванов Иван Иванович 3', 'Петр Петрович Петров 3')" % (
            week_date[0]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '20:15', '20:45', 'Иванов Иван Иванович 4', 'Петр Петрович Петров 2')" % (
            week_date[0]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '18:00', '19:00', 'Иванов Иван Иванович 2', 'Петр Петрович Петров 1')" % (
            week_date[1]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '18:15', '18:30', 'Иванов Иван Иванович 1', 'Петр Петрович Петров 5')" % (
            week_date[1]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '17:30', '18:30', 'Иванов Иван Иванович 4', 'Петр Петрович Петров 4')" % (
            week_date[1]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '12:15', '12:30', 'Иванов Иван Иванович 3', 'Петр Петрович Петров 3')" % (
            week_date[2]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '20:30', '21:00', 'Иванов Иван Иванович 2', 'Петр Петрович Петров 6')" % (
            week_date[2]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '14:45', '15:30', 'Иванов Иван Иванович 1', 'Петр Петрович Петров 6')" % (
            week_date[2]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '16:20', '17:05', 'Иванов Иван Иванович 4', 'Петр Петрович Петров 5')" % (
            week_date[3]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '18:30', '19:00', 'Иванов Иван Иванович 2', 'Петр Петрович Петров 4')" % (
            week_date[3]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '12:00', '13:00', 'Иванов Иван Иванович 1', 'Петр Петрович Петров 3')" % (
            week_date[3]))
    cur.execute(
        "INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name) VALUES ("
        "'%s', '15:45', '16:00', 'Иванов Иван Иванович 4', 'Петр Петрович Петров 2')" % (
            week_date[3]))

    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, "Тестовая база данных заполнена")


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    button_consultation = types.KeyboardButton('Записаться на консультацию')
    markup.add(button_consultation)
    bot.send_message(message.chat.id, 'Здравствуйте, я бот Аркана 🌙', reply_markup=markup, )
    bot.register_next_step_handler(message, consultation_name)


def consultation_name(message):
    bot.register_next_step_handler(message, confirmation_name)
    bot.send_message(message.chat.id, "Как к вам обращаться?", reply_markup=types.ReplyKeyboardRemove())


def confirmation_name(message):
    bot.register_next_step_handler(message, yes_or_no)
    global current_name
    current_name = message.text.strip()
    markup = types.ReplyKeyboardMarkup()
    btn_yes = types.KeyboardButton('Да')
    btn_no = types.KeyboardButton('Нет')
    markup.add(btn_yes, btn_no)
    bot.send_message(message.chat.id, "{}\nВсе верно?".format(current_name), reply_markup=markup)


def yes_or_no(message):
    global current_name
    if message.text == "Да":
        conn = sqlite3.connect('arkana_data_base.sql')
        cur = conn.cursor()
        cur.execute('SELECT name FROM users WHERE name = "%s"' % (current_name))

        if len(cur.fetchall()) == 0:
            cur.execute('INSERT INTO users (name) VALUES ("%s")' % (current_name))

        conn.commit()
        cur.close()
        conn.close()
        choice_of_direction(message)

    else:

        bot.send_message(message.chat.id, "Как к вам обращаться?")
        bot.register_next_step_handler(message, confirmation_name)


def choice_of_direction(message):
    markup = types.ReplyKeyboardMarkup()
    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM directions')
    directions = cur.fetchall()

    for i in directions:
        button_directions = types.KeyboardButton(str(i[1]))
        markup.add(button_directions)

    cur.close()
    conn.close()
    bot.send_message(message.chat.id, current_name + ' ' + "На какое направление хотите записаться?",
                     reply_markup=markup)
    bot.register_next_step_handler(message, choice_of_specialist)


def choice_of_specialist(message):
    global chosen_direction
    markup = types.ReplyKeyboardMarkup()
    chosen_direction = message.text
    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()
    cur.execute("SELECT name "
                "FROM specialists "
                "WHERE direction = '%s'"
                % (chosen_direction))
    specialist = cur.fetchall()

    for i in specialist:
        button_specialist = types.KeyboardButton(str(i[0]))
        markup.add(button_specialist)

    # markup.add(types.KeyboardButton('Любой'))

    cur.close()
    conn.close()

    bot.send_message(message.chat.id,
                     "Отлично, в этом направлении работают несколько специалистов. К кому вас записать?",
                     reply_markup=markup)
    bot.register_next_step_handler(message, date_picker)


def date_picker(message):
    global selected_specialist
    selected_specialist = message.text
    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()

    cur.execute(
        'SELECT consultations.date_consultation, consultations.specialist_name, '
        'consultations.time_begin, consultations.time_end '
        'FROM specialists, consultations '
        'WHERE consultations.specialist_name = specialists.name '
        'AND specialists.direction = "%s" AND consultations.specialist_name = "%s" '
        'ORDER BY consultations.date_consultation ASC' % (chosen_direction, selected_specialist))
    specialist_and_date = cur.fetchall()

    cur.execute("SELECT name "
                "FROM specialists "
                "WHERE direction = '%s'"
                % (chosen_direction))

    specialist = cur.fetchall()

    cur.close()
    conn.close()
    global possible_dates
    possible_dates = []

    specialist_check = {}
    if selected_specialist == "Любой":
        for i in specialist:
            k = i[0]
            specialist_check[k] = []

    else:
        specialist_check[selected_specialist] = []

    supplement_of_the_week = []
    for i in specialist_and_date:
        # print(i)
        supplement_of_the_week.append(i[0])
    current_date = (date.today())

    not_working_day = []
    for i in range(4):
        date_in_question = str(current_date + timedelta(days=i))
        if not date_in_question in supplement_of_the_week:
            not_working_day.append(date_in_question)
    # print(not_working_day)
    displaying_dates_and_times = {}

    for i in specialist_and_date:

        if i[1] == selected_specialist:
            a = (i[0], i[1])
            if a in displaying_dates_and_times:
                displaying_dates_and_times[i[0], i[1]].append((i[2], i[3]))
            else:
                displaying_dates_and_times[i[0], i[1]] = [(i[2], i[3])]

    for i in not_working_day:
        displaying_dates_and_times[i, selected_specialist] = []
    displaying_dates_and_times_str = 'Свободное время специалиста:\n'
    displaying_dates_and_times_list = []

    # print(displaying_dates_and_times)

    for i in displaying_dates_and_times:
        # print(i, displaying_dates_and_times[i])
        if len(displaying_dates_and_times[i]) == 0:
            displaying_dates_and_times_list.append("{}\n".format(i[0][8:] + '.' + i[0][5:7] + '.' + i[0][:4]))
            displaying_dates_and_times_list[-1] += ' • 11:00-20:00\n'

        else:
            displaying_dates_and_times_list.append("{}\n".format(i[0][8:] + '.' + i[0][5:7] + '.' + i[0][:4]))
            displaying_dates_and_times[i].sort()
            if int(displaying_dates_and_times[i][0][0][:2]) >= 12:
                first_work_time = displaying_dates_and_times[i][0][0][:2] + \
                                  displaying_dates_and_times[i][0][0][2:]
                displaying_dates_and_times_list[-1] += ' • 11:00-{}\n'.format(first_work_time)

            count_consultation = len(displaying_dates_and_times[i])
            for j in range(count_consultation - 1):
                begin_chill = displaying_dates_and_times[i][j][1]
                end_chill = displaying_dates_and_times[i][j + 1][0][:2] + \
                            displaying_dates_and_times[i][j + 1][0][2:]

                displaying_dates_and_times_list[-1] += ' • {}-{}\n'.format(begin_chill, end_chill)
            if (displaying_dates_and_times[i][-1][1][:2] == '20' and (
                    displaying_dates_and_times[i][-1][1][2:]) != '00') or not displaying_dates_and_times[i][-1][1][
                                                                              :2] == '21':
                displaying_dates_and_times_list[-1] += ' • {}-21:00\n'.format(displaying_dates_and_times[i][-1][1])

    for i in displaying_dates_and_times_list:
        print(i)

    displaying_dates_and_times_list = my_sort(displaying_dates_and_times_list)

    for i in displaying_dates_and_times_list:
        possible_dates.append(i[:10])

    for i in displaying_dates_and_times_list:
        displaying_dates_and_times_str += i
    bot.send_message(message.chat.id, displaying_dates_and_times_str)

    markup = types.ReplyKeyboardMarkup()
    for i in possible_dates:
        button_directions = types.KeyboardButton(i)
        markup.add(button_directions)
    bot.send_message(message.chat.id, "Какого числа вам будет удобно?", reply_markup=markup)
    bot.register_next_step_handler(message, consultation_time)


def consultation_time(message):
    global selected_date
    selected_date = message.text
    bot.send_message(message.chat.id, 'В какое время хотите начать?', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, choice_of_duration)


def choice_of_duration(message):
    global consultation_start
    consultation_start = message.text
    markup = types.ReplyKeyboardMarkup()
    btn10 = types.KeyboardButton('🌘 10 минут (Бесплатно)')
    btn30 = types.KeyboardButton('🌗 30 минут (550р)')
    btn45 = types.KeyboardButton('🌖 45 минут (1050р)')
    btn60 = types.KeyboardButton('🌕 60 минут (1550р)')
    markup.add(btn10, btn30, btn45, btn60)
    bot.send_message(message.chat.id, 'Выберете продолжительность консультации', reply_markup=markup)
    bot.register_next_step_handler(message, time_check)


def time_check(message):
    global selected_specialist, selected_date, consultation_start, selected_time_begin_end
    consultation_duration = str(int(message.text[2:5]) - 1)

    conn = sqlite3.connect('arkana_data_base.sql')
    cur = conn.cursor()

    cur.execute(
        'SELECT time_begin, time_end '
        'FROM consultations '
        'WHERE specialist_name = "%s" '
        'AND date_consultation = "%s"'
        % (selected_specialist, selected_date[6:] + '-' + selected_date[3:5] + '-' + selected_date[:2]))
    list_of_timespans = cur.fetchall()

    cur.close()
    conn.close()

    if len(consultation_start) == 5:
        selected_time_begin_end.append(consultation_start[:2] + ':' + consultation_start[3:])
        consultation_start = consultation_start[:2] + ':' + consultation_start[3:]
    else:
        selected_time_begin_end.append(consultation_start[:2] + ':00')
        consultation_start = consultation_start[:2] + ':00'

    if int(consultation_start[3:5]) + int(consultation_duration) >= 60:
        selected_time_begin_end.append(str(int(consultation_start[:2]) + 1) + ':' + str(
            int(consultation_start[3:]) + int(consultation_duration) - 60))
    else:
        selected_time_begin_end.append(str(int(consultation_start[:2])) + ':' + str(
            int(consultation_start[3:]) + int(consultation_duration)))
    if len(selected_time_begin_end[1]) == 4:
        selected_time_begin_end[1] += '0'

    #print(selected_time_begin_end)
    #print('----')
    #print(list_of_timespans)

    for i in list_of_timespans:

        if selected_time_begin_end[0] <= i[0] <= selected_time_begin_end[1] or selected_time_begin_end[0] <= i[1] < \
                selected_time_begin_end[1] or (
                selected_time_begin_end[0] <= i[0] and i[1] <= selected_time_begin_end[1]):
            bot.register_next_step_handler(message, choice_of_duration)
            selected_time_begin_end = []
            bot.send_message(message.chat.id, 'В данное время специалист занят, в какое иное время хотите начать?',
                             reply_markup=types.ReplyKeyboardRemove())
            break
    else:
        data_confirmation(message)


def data_confirmation(message):
    global current_name, chosen_direction, selected_date, selected_specialist, consultation_duration, consultation_start
    consultation_duration = message.text[2:5]
    duration_symbol = message.text[:2]
    final_data = '{}, вы записаны на <i>{}</i> <b>{}</b> в <b>{}</b> к <i>{}</i>, ' \
                 'консультация продлится {} минут {}'.format(
        current_name, chosen_direction, selected_date, selected_specialist, consultation_start, consultation_duration,
        duration_symbol)
    markup = types.ReplyKeyboardMarkup()
    btn_yes = types.KeyboardButton('Да')
    btn_no = types.KeyboardButton('Нет')
    markup.add(btn_yes, btn_no)
    bot.send_message(message.chat.id, final_data, reply_markup=markup)
    bot.register_next_step_handler(message, final_confirmation)


def final_confirmation(message):
    global selected_date, selected_specialist, selected_time_begin_end, current_name, chosen_direction, possible_dates, consultation_start, consultation_duration

    if message.text == "Да":
        selected_date_for_db = selected_date[6:] + '-' + selected_date[3:5] + '-' + selected_date[:2]
        conn = sqlite3.connect('arkana_data_base.sql')
        cur = conn.cursor()

        cur.execute('INSERT INTO consultations (date_consultation, time_begin, time_end, user_name, specialist_name)'
                    ' VALUES ("%s", "%s", "%s", "%s", "%s")' % (
                        selected_date_for_db, selected_time_begin_end[0], selected_time_begin_end[1], current_name,
                        selected_specialist))

        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(message.chat.id,
                         'Вы успешно записаны, чтобы записаться повторно просто введите команду /Записаться_на_консультацию',
                         reply_markup=types.ReplyKeyboardRemove())

    chosen_direction = ''
    possible_dates = []
    selected_date = ''
    consultation_start = ''
    consultation_duration = ''
    selected_specialist = ''
    selected_time_begin_end = []

    if message.text == 'Нет':
        choice_of_direction(message)


@bot.message_handler(commands=['Записаться_на_консультацию'])
def sign_up_for_a_consultation(message):
    consultation_name(message)


@bot.message_handler(commands=['error'])
def error(message):
    a = '6' + 5


@bot.message_handler(commands=['id'])
def id(message):
    bot.send_message(message.chat.id, str(message.chat.id))


def my_sort(times_and_dates_list):
    new_list = []
    for i in times_and_dates_list:
        key_list = i[:10].split('.')
        #print(key_list)
        key_str = key_list[2] + key_list[1] + key_list[0]
        #print(key_str)
        new_list.append((key_str, i))
        #print(i)
    new_list.sort()
    final_list = []
    for i in new_list:
        print(i[1])
        final_list.append(i[1])
    return final_list

while True:

    try:
        bot.polling(non_stop=True)

    except Exception as err:

        date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        bot.send_message(972077443, str(date_time) + '---' + str(err))
