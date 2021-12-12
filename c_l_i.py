import json
import os
import telebot
import typer
import aiomysql
import asyncio
from dotenv import load_dotenv
import matplotlib.pyplot as plt

app = typer.Typer()
load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))


@app.command()
def send_poll(question_group: int = typer.Option(..., help="It should be integer value"),
              question_number: int = typer.Option(..., help="Question number in question group"),
              question_text: str = typer.Option(..., help="It's string value for your question"),
              option_1: str = typer.Option(..., help="First option in poll"),
              option_2: str = typer.Option(..., help="Second option in poll"),
              option_3: str = typer.Option(..., help="Third option in poll"),
              option_4: str = typer.Option(..., help="Fourth option in poll"),
              option_5: str = typer.Option(..., help="Fifth option in poll"),
              correct_option: int = typer.Option(..., help="It's correct option in poll from 0 to 4"),
              open_time: int = typer.Option(604800, help="It's optional, because default value is 7 days in seconds")):
    """
        ---- Send poll ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_poll_async(loop, question_group, question_number, question_text, option_1,
                                            option_2, option_3, option_4, option_5, correct_option, open_time))


async def send_poll_async(loop, question_group, question_number, question_text, option_1,
                          option_2, option_3, option_4, option_5, correct_option, open_time):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    options = json.dumps([option_1, option_2, option_3, option_4, option_5])
    if question_number > 0 and question_group > 0:
        sql = f"SELECT * FROM webBot_simplepoll where question_group = {question_group} and question_number= {question_number} "
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                polls = await cur.fetchall()

        if len(polls) == 0:
            sql = "SELECT * FROM webBot_chatuser"
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    users = await cur.fetchall()

            if question_number > 0 and question_group > 0 and 0 <= correct_option < 5 and open_time > 0:
                for user in users:
                    current_poll = bot.send_poll(user[1], question_text,
                                                 json.loads(options),
                                                 correct_option_id=correct_option,
                                                 open_period=open_time)
                    sql = "INSERT INTO webBot_simplepoll  " \
                          "(message_id, poll_id,question_group,question," \
                          "options,correct_option,open_period," \
                          "user_id_id, user_choice, is_closed, question_number) " \
                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    val = [current_poll.poll.id, current_poll.id, question_group, question_text,
                           options, correct_option, open_time, user[0], -1, False, question_number]
                    async with pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(sql, val)
                            await conn.commit()

            else:
                print("Invalid input.")
        else:
            print("This question number exists in this question group")
    else:
        print("Invalid data.")

    pool.close()
    await pool.wait_closed()


@app.command()
def close_poll(chat_id: int = typer.Option(..., help="User chat id"),
               message_id: int = typer.Option(..., help="Message id")):
    """
        ---- Close poll for one user ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(close_poll_async(loop, chat_id, message_id))


async def close_poll_async(loop, chat_id, message_id):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    try:
        message = bot.stop_poll(chat_id, message_id)
    except:
        print()

    sql = f"UPDATE webBot_simplepoll SET is_closed = {int(1)} WHERE poll_id = {message_id}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            await conn.commit()

    pool.close()
    await pool.wait_closed()


@app.command()
def add_group(group_number: str = typer.Option(..., help="Group number"),
              group_course: int = typer.Option(..., help="Group course"),
              students: int = typer.Option(..., help="Number of students in group")):
    """
        ---- Add group ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(add_group_async(loop, group_number, group_course, students))


async def add_group_async(loop, group_number, group_course, students):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    sql = "INSERT INTO webBot_group  (group_number, group_course, number_of_students) VALUES (%s, %s, %s)"
    val = [group_number, group_course, students]
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, val)
            await conn.commit()

    pool.close()
    await pool.wait_closed()


@app.command()
def add_student(f_n: str = typer.Option(..., help="First name"),
                l_n: str = typer.Option(..., help="Last name"),
                gr_num: str = typer.Option(..., help="Group number"),
                l_num: int = typer.Option(..., help="List number in group")):
    """
        ---- Add student ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(add_student_async(loop, f_n, l_n, gr_num, l_num))


async def add_student_async(loop, f_n, l_n, gr_num, l_num):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    sql = f"SELECT * FROM webBot_group where group_number = {gr_num}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            group = await cur.fetchall()

    if len(group) > 0:
        group = group[0]
    else:
        pool.close()
        await pool.wait_closed()
        print("There is no such group.")
        return

    if 0 < l_num < group[3]:
        sql = "INSERT INTO webBot_student  (first_name, last_name, group_id_id, list_number) VALUES (%s, %s, %s, %s)"
        val = [f_n, l_n, group[0], l_num]
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, val)
                await conn.commit()
    else:
        pool.close()
        await pool.wait_closed()
        print("Invalid list number")
        return


@app.command()
def delete_group(gr_num: str = typer.Option(..., help="Group number")):
    """
        ---- Delete group ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(delete_group_async(loop, gr_num))


async def delete_group_async(loop, gr_num):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    sql = f"SELECT * FROM webBot_group where group_number = {gr_num}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            group = await cur.fetchall()

    if len(group) > 0:
        sql = f"DELETE FROM webBot_student WHERE group_id_id = {group[0][0]}"
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                await conn.commit()

        sql = f"DELETE FROM webBot_group WHERE group_number = {gr_num}"
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                await conn.commit()

        pool.close()
        await pool.wait_closed()

    else:
        pool.close()
        await pool.wait_closed()
        print(f"There isn't group. Try again.")
        return


@app.command()
def delete_student(l_n: str = typer.Option(..., help="Last name"),
                   gr_num: str = typer.Option(..., help="Group number"),
                   l_num: int = typer.Option(..., help="List number in group")):
    """
        ---- Delete student ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(delete_student_async(loop, l_n, gr_num, l_num))


async def delete_student_async(loop, l_n, gr_num, l_num):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    sql = f"SELECT * FROM webBot_group where group_number = {gr_num}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            group = await cur.fetchall()

    if len(group) > 0:
        sql = f"SELECT * FROM webBot_student WHERE last_name = '{l_n}'"
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                student = await cur.fetchall()

        if len(student) > 0:
            sql = f"DELETE FROM webBot_student WHERE group_id_id = {group[0][0]} and " \
                  f"list_number = {l_num} "

            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    await conn.commit()

        else:
            print(f"There's no such student. Try again.")

        pool.close()
        await pool.wait_closed()
    else:
        pool.close()
        await pool.wait_closed()
        print(f"There isn't group. Try again.")
        return


@app.command()
def delete_chat_user(chat_id: int = typer.Option(..., help="User chat id")):
    """
        ---- Delete user ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(delete_chat_user_async(loop, chat_id))


async def delete_chat_user_async(loop, chat_id):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    sql = f"SELECT * FROM webBot_chatuser WHERE tg_chat_id = {chat_id}"
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            user = await cur.fetchall()

    if len(user) > 0:
        sql = f"DELETE FROM webBot_chatuser WHERE tg_chat_id = {chat_id}"

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                await conn.commit()

        sql = f"DELETE FROM webBot_registrationstate WHERE tg_chat_id = {chat_id}"

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                await conn.commit()

    else:
        print(f"There's no such chat-user. Try again.")

    pool.close()
    await pool.wait_closed()


@app.command()
def close_question_group(q_gr: int = typer.Option(..., help="Question group")):
    """
        ---- Close question group ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(close_question_group_async(loop, q_gr))


async def close_question_group_async(loop, q_gr):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    sql = f"SELECT * FROM webBot_simplepoll where question_group = {q_gr}"

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            questions = await cur.fetchall()

    for question in questions:
        if question[10] == 0:
            sql = f"SELECT * FROM webBot_chatuser WHERE id = {question[9]}"

            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    user = await cur.fetchall()

            message = bot.stop_poll(user[0][1], question[2])

            sql = f"UPDATE webBot_simplepoll SET is_closed = {int(1)} WHERE poll_id = {question[2]}"
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    await conn.commit()

    pool.close()
    await pool.wait_closed()


@app.command()
def get_question_result(q_gr: int = typer.Option(..., help="Question group"),
                        q_num: int = typer.Option(..., help="Question number in question group")):
    """
    ---- Get histogram for one question , question should be closed ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_question_result_async(loop, q_gr, q_num))


async def get_question_result_async(loop, q_gr, q_num):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    if q_gr > 0 and q_num > 0:
        correct_answer = [0, 0, 0, 0, 0]
        wrong_answer = [0, 0, 0, 0, 0]
        sql = f"SELECT * FROM webBot_simplepoll where question_group = {q_gr} and question_number= {q_num}"
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                questions = await cur.fetchall()

        sql = f"SELECT id FROM webBot_chatuser "
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                users = await cur.fetchall()

        total_ans = len(users)
        if total_ans == 0:
            print("No users.")
            return
        else:
            for question in questions:
                if question[8] == question[6] and question[10] == 1:
                    correct_answer[question[8]] += 1
                else:
                    if question[10] == 1:
                        wrong_answer[question[8]] += 1

            plt.figure(figsize=(10, 10), num='Histogram')

            plt.ylim([0, 1])
            per = []
            x_list = []
            for i in range(len(correct_answer)):
                per.append((correct_answer[i] + wrong_answer[i]) / float(total_ans))
                x_list.append(i)

            plt.bar(x_list, per)
            plt.savefig('histogram.png')
            if correct_answer == 0 and wrong_answer == 0:
                print("There's no such question group or question number. Try again.")
            else:
                print(correct_answer)
                print(wrong_answer)
    else:
        print("There's no such question group or question number. Try again.")

    pool.close()
    await pool.wait_closed()


@app.command()
def send_text_question(question: str = typer.Option(..., help="Question text"),
                       q_num: int = typer.Option(..., help="Question number")):
    """
    ---- Send text question ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_text_question_async(loop, question, q_num))


async def send_text_question_async(loop, question, q_num):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    if q_num > 0:
        sql = f"SELECT * FROM webBot_textquestion where question_number= {q_num}"

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                t_question = await cur.fetchall()

        if len(t_question) == 0:
            sql = "SELECT * FROM webBot_chatuser"
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    users = await cur.fetchall()

            for user in users:
                current_question = bot.send_message(user[1], question)
                sql = "INSERT INTO webBot_textquestion  " \
                      "(message_id, question, question_number,user_id_id, user_answer, user_image, is_closed) " \
                      "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                val = [current_question.id, question, q_num, user[0], "", "", False]
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(sql, val)
                        await conn.commit()

        else:
            print("This question number exist.")
    else:
        print("Invalid data.")

    pool.close()
    await pool.wait_closed()


@app.command()
def close_text_question(q_num: int = typer.Option(..., help="The number of the question you want to close.")):
    """
    ---- Close text question ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(close_text_question_async(loop, q_num))


async def close_text_question_async(loop, q_num):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)
    if q_num > 0:
        sql = f"SELECT * FROM webBot_textquestion where question_number = {q_num} and is_closed = {0}"
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                questions = await cur.fetchall()

        if len(questions) > 0:
            for question in questions:
                sql = f"UPDATE webBot_textquestion SET is_closed = {1} WHERE id = {question[0]}"
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(sql)
                        await conn.commit()

        else:
            print("There's no such question number. Try again.")
    else:
        print("Invalid data.")

    pool.close()
    await pool.wait_closed()


@app.command()
def get_result_question_group(q_gr: int = typer.Option(..., help="Question group")):
    """
    ---- Simple question group results ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_result_question_group_async(loop, q_gr))


async def get_result_question_group_async(loop, q_gr):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    if q_gr > 0:
        result = []
        sql = "SELECT * FROM webBot_chatuser"
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                users = await cur.fetchall()

        if len(users) > 0:
            for user in users:
                sql = f"SELECT * FROM webBot_student where id = {user[2]}"
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(sql)
                        student = await cur.fetchall()

                student = student[0]

                sql = f"SELECT correct_option, user_choice, is_closed FROM webBot_simplepoll where user_id_id = {user[0]}" \
                      f" and question_group = {q_gr} "

                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(sql)
                        res = await cur.fetchall()

                cor_ans = 0
                wr_ans = 0

                for item in res:
                    if item[0] == item[1] and item[2] == 1:
                        cor_ans += 1
                    else:
                        if item[2] == 1:
                            wr_ans += 1
                result.append([student[2], student[1], f"{cor_ans}/{cor_ans + wr_ans}"])
            print(result)
        else:
            print("There aren't students.")
    else:
        print("Invalid data.")

    pool.close()
    await pool.wait_closed()


@app.command()
def get_text_question_result(q_num: int = typer.Option(..., help="Question number")):
    """
    ---- Download the result of the text question ----
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_text_question_result_async(loop, q_num))


async def get_text_question_result_async(loop, q_num):
    pool = await aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                      user=os.getenv("DB_USER"),
                                      password=os.getenv("DB_PASSWORD"), db=os.getenv("DB_NAME"), loop=loop)

    if q_num > 0:
        current_path = os.getcwd()
        current_path += "/results/"
        sql = "SELECT * FROM webBot_chatuser"

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                users = await cur.fetchall()

        if len(users) > 0:
            for user in users:

                sql = f"SELECT first_name, last_name, group_number FROM webBot_student left join webBot_group on " \
                      f"webBot_student.group_id_id = webBot_group.id where webBot_student.id = {user[2]} "
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(sql)
                        student = await cur.fetchall()

                student = student[0]

                sql = f"SELECT user_answer, user_image, is_closed, question FROM webBot_textquestion where user_id_id = {user[0]}" \
                      f" and question_number = {q_num}"
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(sql)
                        questions = await cur.fetchall()

                target_path = f"{student[2]}/{student[1]} {student[0]}/"
                directory = current_path + target_path
                if not os.path.isdir(directory):
                    os.makedirs(directory)

                for item in questions:
                    if item[2] == 1:
                        if item[0] != "":
                            with open(directory + f"{student[2]}.{student[1]}_{student[0]}.txt", 'w') as file:
                                answer = f"Question: {item[3]} \n Answer: {item[0]}\n"
                                file.write(answer)

                        if item[1] != "":
                            image_dict = json.loads(item[1])
                            file_info = bot.get_file(image_dict['file_id'])
                            image = bot.download_file(file_info.file_path)
                            with open(directory + f"question_{q_num}.png", 'wb') as file:
                                file.write(image)
                    else:
                        print("Question should be closed.")
        else:
            print("There aren't students.")
    else:
        print("Invalid question number.")

    pool.close()
    await pool.wait_closed()


if __name__ == '__main__':
    app()
