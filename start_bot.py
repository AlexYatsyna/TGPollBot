import asyncio
import json
import os
import telebot
import mysql.connector
from asgiref.sync import sync_to_async
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

isAuth = False
isGroupSelected = False
isStart = False
groups = []
group_number = -1
user = []

connection = mysql.connector.connect(host=os.getenv("DB_HOST"),
                                     database=os.getenv("DB_NAME"),
                                     user=os.getenv("DB_USER"),
                                     password=os.getenv("DB_PASSWORD"))
my_cursor = connection.cursor()


def show_groups(chat_id):
    global groups, my_cursor
    try:

        sql = "SELECT * FROM webBot_group"
        my_cursor.execute(sql)
        groups = my_cursor.fetchall()
        answ = "Choose your group:\n"

        for item in groups:
            answ += str(item[0]) + ". " + item[1] + "\n"

        bot.send_message(chat_id, answ)
    except Error as e:
        print("Error while connecting to MySQL", e)


def show_students(chat_id, group_id):
    global group_number, my_cursor, isStart, isGroupSelected
    try:
        my_cursor = connection.cursor()
        sql = f"SELECT * FROM webBot_student where group_id_id = {group_id}"
        group_number = group_id
        my_cursor.execute(sql)
        students = my_cursor.fetchall()
        if len(students) > 0:
            answ = "Choose your number:\n"

            for item in students:
                answ += str(item[0]) + ". " + item[1] + " " + item[2] + "\n"

            bot.send_message(chat_id, answ)
            isGroupSelected = True
        else:
            bot.send_message(chat_id, "Wrong group selected. Try again")
            isStart = False
            isGroupSelected = False

    except Error as e:
        print("Error while connecting to MySQL", e)


def auth(chat_id, student_id):
    global isAuth, isStart, isGroupSelected, my_cursor
    try:
        my_cursor = connection.cursor()
        sql = f"SELECT * FROM webBot_student where id = {student_id} and group_id_id = {group_number}"
        my_cursor.execute(sql)
        student = my_cursor.fetchall()
        if len(student) > 0:

            sql = f"SELECT * FROM webBot_chatuser where student_id_id = {student[0][0]}"
            my_cursor.execute(sql)
            chat_user = my_cursor.fetchall()

            if len(chat_user) == 1:
                if chat_user[0][1] == chat_id:
                    bot.send_message(chat_id, "You're already sign in")
                    isAuth = True
                else:
                    bot.send_message(chat_id, "Contact the teacher")

            else:
                sql = "INSERT INTO webBot_chatuser  (tg_chat_id, student_id_id) VALUES (%s, %s)"
                val = [chat_id, str(student[0][0])]
                my_cursor.execute(sql, val)
                connection.commit()
                isAuth = True
        else:
            bot.send_message(chat_id, "Wrong student selected. Try again")
            isAuth = False
            isStart = False
            isGroupSelected = False
    except Error as e:
        isAuth = False
        isStart = False
        isGroupSelected = False
        print("Error while connecting to MySQL", e)


@sync_to_async()
def checkAuth(chat_id):
    global isAuth, user, my_cursor
    try:
        my_cursor = connection.cursor()
        sql = f"SELECT * FROM webBot_chatuser where tg_chat_id = {chat_id}"
        my_cursor.execute(sql)
        chat_user = my_cursor.fetchall()
        if len(chat_user) == 1:
            user = chat_user
            isAuth = True
        else:
            isAuth = False

    except Error as e:
        isAuth = False
        print("Error while connecting to MySQL", e)


def poll_updater(poll):
    cur_state = 0
    user_choice = -1
    sql = f"SELECT * FROM webBot_simplepoll where message_id = {poll.id}"
    my_cursor.execute(sql)
    poll_db = my_cursor.fetchall()[0]

    if (poll_db[10] == 0 and poll.is_closed == False) or (poll_db[10] == 1 and poll.is_closed == True):
        cur_state = poll_db[10]
        counter = 0
        for option in poll.options:
            if option.voter_count == 1:
                user_choice = counter
                break
            else:
                counter += 1
    else:
        if poll_db[10] == 0 and poll.is_closed == True:
            user_choice = poll_db[8]
            cur_state = 1
        else:
            user_choice = poll_db[8]
            cur_state = 0

    sql = f"UPDATE webBot_simplepoll SET user_choice = {user_choice} , is_closed = {cur_state} WHERE id = {poll_db[0]}"
    my_cursor.execute(sql)
    connection.commit()


@sync_to_async()
def text_response(message):
    answer = message.text
    sql = f"SELECT * FROM webBot_textquestion where message_id = {message.reply_to_message.id}"
    my_cursor.execute(sql)
    question = my_cursor.fetchall()
    if len(question) > 0:
        if question[0][6] == 0:
            sql = f"UPDATE webBot_textquestion SET user_answer = '{answer}' WHERE id = {question[0][0]}"
            my_cursor.execute(sql)
            connection.commit()
        else:
            bot.send_message(message.chat.id, "Question is already closed.")


@sync_to_async
def image_response(message):
    if len(message.photo) == 1:
        image = message.photo[1]
    else:
        image = message.photo[len(message.photo)-1]
    dictionary_img = {'file_id': image.file_id, 'file_size': image.file_size, 'file_unique_id': image.file_unique_id,
                      'height': image.height, 'width': image.width}
    print(image.file_id)
    sql = f"SELECT * FROM webBot_textquestion where message_id = {message.reply_to_message.id}"
    my_cursor.execute(sql)
    question = my_cursor.fetchall()
    if len(question) > 0:
        if question[0][6] == 0:
            sql = f"UPDATE webBot_textquestion SET user_image = '{json.dumps(dictionary_img)}' WHERE id = {question[0][0]}"
            my_cursor.execute(sql)
            connection.commit()
        else:
            bot.send_message(message.chat.id, "Question is already closed.")


@bot.message_handler(content_types=['image', 'photo'])
def image_answer_handler(message):
    if message.reply_to_message is not None:
        asyncio.run(image_response(message))


@bot.poll_handler(poll_updater)
@bot.message_handler(content_types=['text'])
def echo(message):
    global isAuth, isStart, isGroupSelected
    asyncio.run(checkAuth(message.chat.id))
    if ((message.text == "/start") or (message.text == "/signup")) and not isAuth:
        isStart = True
        show_groups(message.chat.id)

    elif message.text.isdigit() and not isAuth and not isGroupSelected and isStart:

        if 0 < int(message.text):
            show_students(message.chat.id, int(message.text))
        else:
            bot.send_message(message.chat.id, "Invalid group, try again")
            isStart = False

    elif message.text.isdigit() and not isAuth and isGroupSelected and isStart:

        if 0 < int(message.text):
            auth(message.chat.id, int(message.text))
        else:
            bot.send_message(message.chat.id, "Invalid student number, try again")
            isStart = False
            isGroupSelected = False
    else:
        if message.reply_to_message is not None:
            asyncio.run(text_response(message))


if __name__ == '__main__':
    bot.polling()
