import asyncio
import json
import aiomysql
import os
import telebot

from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

groups = []
group_number = -1
user = []


async def show_groups(chat_id, loop):
    global groups

    sql = "SELECT * FROM webBot_group"
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            groups = await cur.fetchall()
    pool.close()
    await pool.wait_closed()

    answ = "Choose your group:\n"

    for item in groups:
        if item[1] == "000000":
            continue
        answ += str(item[0]) + ". " + item[1] + "\n"

    bot.send_message(chat_id, answ)


async def show_students(chat_id, group_id, loop):
    global group_number

    sql = f"SELECT * FROM webBot_student where group_id_id = {group_id}"
    group_number = group_id
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            students = await cur.fetchall()
    pool.close()
    await pool.wait_closed()

    if len(students) > 0:
        answ = "Choose your number:\n"

        for item in students:
            answ += str(item[0]) + ". " + item[1] + " " + item[2] + "\n"
        bot.send_message(chat_id, answ)

        return True
    else:
        bot.send_message(chat_id, "Wrong group selected. Try again")
        return False


async def auth(chat_id, student_id, loop):
    sql = f"SELECT * FROM webBot_student where id = {student_id} and group_id_id = {group_number}"

    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            student = await cur.fetchall()

    if len(student) > 0:

        sql = f"SELECT * FROM webBot_chatuser where student_id_id = {student[0][0]}"

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                chat_user = await cur.fetchall()

        if len(chat_user) == 1:
            if chat_user[0][1] == chat_id:
                bot.send_message(chat_id, "You're already sign in")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(set_current_state(chat_id, 2, 'auth', loop, chat_user[0][2]))
            else:
                bot.send_message(chat_id, "Contact the teacher")

        else:
            sql = "INSERT INTO webBot_chatuser  (tg_chat_id, student_id_id) VALUES (%s, %s)"
            val = [chat_id, str(student[0][0])]
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql, val)
                    await conn.commit()
            pool.close()
            await pool.wait_closed()
            return student[0][0]

    else:
        pool.close()
        await pool.wait_closed()
        bot.send_message(chat_id, "Wrong student selected. Try again")
        return None


async def poll_updater(poll, loop):
    cur_state = 0
    user_choice = -1
    sql = f"SELECT * FROM webBot_simplepoll where message_id = {poll.id}"
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            poll_db = await cur.fetchone()

    if poll_db is not None:
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
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                await conn.commit()
        pool.close()
        await pool.wait_closed()


async def text_response(message, loop):
    answer = message.text
    sql = f"SELECT * FROM webBot_textquestion where message_id = {message.reply_to_message.id}"
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            question = await cur.fetchall()

    if len(question) > 0:
        if question[0][6] == 0:
            sql = f"UPDATE webBot_textquestion SET user_answer = '{answer}' WHERE id = {question[0][0]}"
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    await conn.commit()
        else:
            bot.send_message(message.chat.id, "Question is already closed.")
    pool.close()
    await pool.wait_closed()


async def image_response(message, loop):
    if len(message.photo) == 1:
        image = message.photo[1]
    else:
        image = message.photo[len(message.photo) - 1]
    dictionary_img = {'file_id': image.file_id, 'file_size': image.file_size, 'file_unique_id': image.file_unique_id,
                      'height': image.height, 'width': image.width}
    print(image.file_id)
    sql = f"SELECT * FROM webBot_textquestion where message_id = {message.reply_to_message.id}"

    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            question = await cur.fetchall()

    if len(question) > 0:
        if question[0][6] == 0:
            sql = f"UPDATE webBot_textquestion SET user_image = '{json.dumps(dictionary_img)}' WHERE id = {question[0][0]}"
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    await conn.commit()

        else:
            bot.send_message(message.chat.id, "Question is already closed.")
    pool.close()
    await pool.wait_closed()


@bot.message_handler(content_types=['image', 'photo'])
def image_answer_handler(message):
    if message.reply_to_message is not None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(image_response(message, loop))


def process_poll(asd):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(poll_updater(asd, loop))


async def set_current_state(chat_id, value, column, loop, student_id=-1):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    if column == "start":
        sql = "INSERT INTO webBot_registrationstate  (tg_chat_id, registration_state) VALUES (%s, %s)"
        val = [chat_id, value]
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, val)
                await conn.commit()

        pool.close()
        await pool.wait_closed()
        return

    if column == 'group_selected':
        sql = f"UPDATE webBot_registrationstate SET registration_state = {value} WHERE tg_chat_id = {chat_id}"

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                await conn.commit()

        pool.close()
        await pool.wait_closed()
        return

    if column == "auth":
        sql = f"UPDATE webBot_registrationstate SET registration_state = {value} WHERE tg_chat_id = {chat_id}"

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                await conn.commit()

        pool.close()
        await pool.wait_closed()
        return


async def get_current_state(chat_id, loop):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    sql = f"SELECT registration_state FROM webBot_registrationstate where tg_chat_id={chat_id}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            result = await cur.fetchone()

    pool.close()
    await pool.wait_closed()
    return result


def get_state(chat_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    state = loop.run_until_complete(get_current_state(chat_id, loop))
    return state


@bot.poll_handler(process_poll)
@bot.message_handler(content_types=['text'])
def echo(message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    current_state = get_state(message.chat.id)
    if current_state is not None:
        current_state = current_state[0]
    if message.text == "/start" and (current_state is None or current_state == -1):
        if current_state is None:
            loop.run_until_complete(set_current_state(message.chat.id, 0, 'start', loop))
        else:
            loop.run_until_complete(set_current_state(message.chat.id, 0, 'group_selected', loop))
        loop.run_until_complete(show_groups(message.chat.id, loop))

    if current_state == 0:
        if message.text.isdigit() and 0 < int(message.text):
            if loop.run_until_complete(show_students(message.chat.id, int(message.text), loop)) is True:
                loop.run_until_complete(set_current_state(message.chat.id, 1, 'group_selected', loop))
            else:
                loop.run_until_complete(set_current_state(message.chat.id, -1, 'group_selected', loop))
        else:
            loop.run_until_complete(set_current_state(message.chat.id, -1, 'group_selected', loop))
            bot.send_message(message.chat.id, "Invalid group, try again")

    if current_state == 1:
        if message.text.isdigit() and 0 < int(message.text):
            student_id = loop.run_until_complete(auth(message.chat.id, int(message.text), loop))
            if student_id is not None:
                loop.run_until_complete(set_current_state(message.chat.id, 2, 'auth', loop, student_id))
                bot.send_message(message.chat.id, "Successfully!")
            else:
                loop.run_until_complete(set_current_state(message.chat.id, -1, 'group_selected', loop))
        else:
            loop.run_until_complete(set_current_state(message.chat.id, -1, 'group_selected', loop))
            bot.send_message(message.chat.id, "Invalid student number, try again")

    if message.reply_to_message is not None:
        loop.run_until_complete(text_response(message, loop))


# @bot.poll_handler(process_poll)
# @bot.message_handler(content_types=['text'])
# async def echo(message):
#     global isAuth, isStart, isGroupSelected
#
#     if not isinstance(message, telebot.types.Poll):
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(checkAuth(message.chat.id, loop))
#
#         if ((message.text == "/start") or (message.text == "/signup")) and not isAuth:
#             isStart = True
#             loop.run_until_complete(show_groups(message.chat.id, loop))
#
#         elif message.text.isdigit() and not isAuth and not isGroupSelected and isStart:
#
#             if 0 < int(message.text):
#                 loop.run_until_complete(show_students(message.chat.id, int(message.text), loop))
#             else:
#                 bot.send_message(message.chat.id, "Invalid group, try again")
#                 isStart = False
#
#         elif message.text.isdigit() and not isAuth and isGroupSelected and isStart:
#
#             if 0 < int(message.text):
#                 loop.run_until_complete(auth(message.chat.id, int(message.text), loop))
#             else:
#                 bot.send_message(message.chat.id, "Invalid student number, try again")
#                 isStart = False
#                 isGroupSelected = False
#         else:
#             if message.reply_to_message is not None:
#                 loop.run_until_complete(text_response(message, loop))


if __name__ == '__main__':
    bot.polling()
