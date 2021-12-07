import json
import os

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import ChatUser
from .forms import *
import matplotlib.pyplot as plt
from webBotInterface.settings import bot


def main_page(request):
    category = ChatUser.objects.all()
    return render(request, 'main/main_page.html', {'cat1': category})


def add_text_question(request):
    if not request.user.is_anonymous:
        if request.method == 'POST':
            form = TextQuestionForm(request.POST)
            if form.is_valid():
                quest = form.save(commit=False)
                question = form.cleaned_data.get('question')
                question_number = form.cleaned_data.get('question_number')
                if question_number < 1:
                    form = TextQuestionForm()
                    return render(request, 'main/for_from.html', {'form': form, 'tittle': "Create and send text "
                                                                                          "question", 'message':
                                                                      "Question number should be > 0 "})
                else:
                    query = TextQuestion.objects.filter(question_number=question_number)
                    if len(query) == 0:
                        users = ChatUser.objects.all()
                        for user in users:
                            message = bot.send_message(user.tg_chat_id, question)
                            print(message.id)
                            t = TextQuestion(message_id=message.id, question=question, question_number=question_number,
                                             user_answer="",
                                             user_image="", user_id=user, is_closed=False)
                            t.save()
                    else:
                        form = TextQuestionForm()
                        return render(request, 'main/for_from.html', {'form': form, 'tittle': "Create and send text "
                                                                                              "question", 'message':
                                                                          "A question with the same number already "
                                                                          "exists."})
                return redirect('home')
        else:
            form = TextQuestionForm()
        return render(request, 'main/for_from.html', {'form': form, 'tittle': "Create and send text question"})
    return redirect('home')


def close_text_question(request):
    if not request.user.is_anonymous:
        if request.method == 'POST':
            form = CloseTextQuestionForm(request.POST)
            if form.is_valid():
                form.save(commit=False)
                question_number = form.cleaned_data.get('question_number')
                number_list = TextQuestion.objects.all().order_by('question_number').values_list(
                    'question_number').distinct()

                if len(number_list.filter(question_number=question_number)) == 0:
                    res = ["There are groups:"]
                    for item in number_list:
                        res.append(f"Question number №{item[0]}")
                    form = CloseTextQuestionForm()
                    return render(request, 'main/for_from.html',
                                  {'form': form, 'list': res, 'tittle': "Close text question",
                                   'message': "Question number does not exist"})
                else:
                    TextQuestion.objects.filter(question_number=question_number).update(is_closed=True)
                return redirect('home')
        else:
            number_list = TextQuestion.objects.all().order_by('question_number').values_list(
                'question_number').distinct()
            res = ["There are groups:"]
            for item in number_list:
                res.append(f"Question number №{item[0]}")
            form = CloseTextQuestionForm()
        return render(request, 'main/for_from.html', {'form': form, 'tittle': "Close text question", 'list': res})
    return redirect('home')


def close_survey(request):
    if not request.user.is_anonymous:
        if request.method == 'POST':
            form = CloseSurveyForm(request.POST)
            if form.is_valid():
                form.save(commit=False)
                question_group = form.cleaned_data.get('question_group')
                group_list = SimplePoll.objects.all().order_by('question_group').values_list(
                    'question_group').distinct()
                if len(group_list.filter(question_group=question_group)) == 0:
                    form = CloseSurveyForm()
                    res = []
                    res.append("There are groups:")
                    for item in group_list:
                        res.append(f"Question group №{item[0]}")
                    return render(request, 'main/for_from.html', {'form': form, 'tittle': "Close survey", 'list': res,
                                                                  'message': "Such a survey does not exist"})
                else:
                    questions = SimplePoll.objects.filter(question_group=question_group)
                    for question in questions:
                        if not question.is_closed:
                            bot.stop_poll(question.user_id.tg_chat_id, question.poll_id)
                    questions.update(is_closed=True)
                return redirect('home')
        else:
            group_list = SimplePoll.objects.all().order_by('question_group').values_list('question_group').distinct()
            res = ["There are groups:"]
            for item in group_list:
                res.append(f"Question group №{item[0]}")
            form = CloseSurveyForm()
        return render(request, 'main/for_from.html', {'form': form, 'tittle': "Close survey", 'list': res})
    return redirect('home')


def send_poll(request):
    if not request.user.is_anonymous:
        if request.method == 'POST':
            form = SendPollForm(request.POST)
            if form.is_valid():

                form.save(commit=False)

                question_group = form.cleaned_data.get('question_group')
                question_number = form.cleaned_data.get('question_number')
                question = form.cleaned_data.get('question')
                op_0 = form.cleaned_data.get('option_0')
                op_1 = form.cleaned_data.get('option_1')
                op_2 = form.cleaned_data.get('option_2')
                op_3 = form.cleaned_data.get('option_3')
                op_4 = form.cleaned_data.get('option_4')
                correct_option = form.cleaned_data.get('correct_option')
                open_time = form.cleaned_data.get('open_period')

                if question_group < 1:
                    form = SendPollForm()
                    return render(request, 'main/for_from.html',
                                  {'form': form, 'tittle': "Send question", 'message': "Question group sould be > 0"})

                checki = SimplePoll.objects.filter(question_number=question_number, question_group=question_group)
                if len(checki) > 0:
                    form = SendPollForm()
                    return render(request, 'main/for_from.html', {'form': form, 'tittle': "Send question",
                                                                  'message': "This question number exists in this question group"})

                if correct_option > 4 or correct_option < 0:
                    form = SendPollForm()
                    return render(request, 'main/for_from.html', {'form': form, 'tittle': "Send question",
                                                                  'message': "Correct option should be from 0 to 4 "})

                if open_time == 0 or open_time < 0:
                    open_time = 604800

                options = json.dumps([op_0, op_1, op_2, op_3, op_4])

                users = ChatUser.objects.all()
                for user in users:
                    message = bot.send_poll(user.tg_chat_id, question,
                                            json.loads(options),
                                            correct_option_id=correct_option,
                                            open_period=open_time)
                    t = SimplePoll(message_id=message.poll.id, poll_id=message.id, question_group=question_group,
                                   question=question, question_number=question_number,
                                   options=options, correct_option=correct_option, open_period=open_time, user_id=user,
                                   user_choice=-1, is_closed=False)
                    t.save()

                return redirect('home')
        else:
            form = SendPollForm()
        return render(request, 'main/for_from.html', {'form': form, 'tittle': "Send question"})
    return redirect('home')


def survey_results(request):
    if not request.user.is_anonymous:
        if request.method == 'POST':
            form = CloseSurveyForm(request.POST)
            if form.is_valid():
                form.save(commit=False)
                question_group = form.cleaned_data.get('question_group')
                group_list = SimplePoll.objects.all().order_by('question_group').values_list(
                    'question_group').distinct()
                if len(group_list.filter(question_group=question_group)) == 0:
                    form = CloseSurveyForm()
                    res = []
                    res.append("There are groups:")
                    for item in group_list:
                        res.append(f"Question group №{item[0]}")
                    return render(request, 'main/for_from.html',
                                  {'form': form, 'tittle': "Get survey results", 'list': res,
                                   'message': "Such a survey does not exist"})
                else:
                    users = ChatUser.objects.all()
                    if len(users) > 0:
                        if len(SimplePoll.objects.filter(question_group=question_group, is_closed=False)) == 0:
                            result = []
                            for user in users:
                                user_question_group = SimplePoll.objects.filter(user_id=user,
                                                                                question_group=question_group).values_list(
                                    'correct_option', 'user_choice')
                                cor_ans = 0
                                wr_ans = 0

                                for question in user_question_group:
                                    if question[0] == question[1]:
                                        cor_ans += 1
                                    else:
                                        wr_ans += 1
                                result.append(
                                    f"{user.student_id.last_name} {user.student_id.first_name} {cor_ans}/{cor_ans + wr_ans}")
                                return render(request, 'main/results.html',
                                              {'list': result})
                        else:
                            return render(request, 'main/results.html',
                                          {'list': ["Question group should be closed"]})
                    return render(request, 'main/results.html',
                                  {'list': ["There aren't users for results"]})


        else:
            group_list = SimplePoll.objects.all().order_by('question_group').values_list('question_group').distinct()
            res = ["There are groups:"]
            for item in group_list:
                res.append(f"Question group №{item[0]}")
            form = CloseSurveyForm()
        return render(request, 'main/for_from.html', {'form': form, 'tittle': "Get survey results", 'list': res})
    return redirect('home')


def get_histogram(request):
    if not request.user.is_anonymous:
        if request.method == 'POST':
            form = HistogramForm(request.POST)
            if form.is_valid():
                form.save(commit=False)
                cur_question_group = form.cleaned_data.get('question_group')
                cur_question_number = form.cleaned_data.get('question_number')
                group_list = SimplePoll.objects.all().order_by('question_group').values_list(
                    'question_group').distinct()
                if len(group_list.filter(question_group=cur_question_group)) == 0 or \
                        len(SimplePoll.objects.filter(question_group=cur_question_group,
                                                      question_number=cur_question_number, is_closed=True)) == 0:
                    form = HistogramForm()
                    res = []
                    res.append("There are groups:")
                    for item in group_list:
                        res.append(f"Question group №{item[0]}")
                    return render(request, 'main/for_from.html', {'form': form, 'tittle': "Get histogram", 'list': res,
                                                                  'message': "Such a survey does not exist"})
                else:
                    correct_answer = [0, 0, 0, 0, 0]
                    wrong_answer = [0, 0, 0, 0, 0]
                    total_ans = 0
                    questions = SimplePoll.objects.filter(question_group=cur_question_group,
                                                          question_number=cur_question_number, is_closed=True). \
                        values_list('correct_option', 'user_choice')
                    for question in questions:
                        if question[0] == question[1]:
                            correct_answer[question[1]] += 1
                            total_ans += 1
                        else:
                            if question[1] != -1:
                                wrong_answer[question[1]] += 1
                                total_ans += 1
                    plt.figure(figsize=(10, 10), num='Histogram')
                    plt.ylim([0, 1])
                    per = []
                    x_list = []
                    for i in range(len(correct_answer)):
                        if total_ans != 0:
                            per.append((correct_answer[i] + wrong_answer[i]) / float(total_ans))
                        else:
                            return render(request, 'main/results.html',
                                          {'list': ["No answers to build a histogram."]})
                        x_list.append(i)
                    plt.bar(x_list, per)
                    plt.savefig(
                        f"{os.path.abspath(os.path.dirname(__name__))}" + f'histogram{cur_question_group}_{cur_question_number}.png')
                return render(request, 'main/results.html', {'list': ["The histogram will be saved in the django "
                                                                      "project folder."]})
        else:
            group_list = SimplePoll.objects.all().order_by('question_group').values_list('question_group').distinct()
            res = ["There are groups:"]
            for item in group_list:
                res.append(f"Question group №{item[0]}")
            form = HistogramForm()
        return render(request, 'main/for_from.html', {'form': form, 'tittle': "Get histogram", 'list': res})
    return redirect('home')


def get_text_result(request):
    if not request.user.is_anonymous:
        if request.method == 'POST':
            form = CloseTextQuestionForm(request.POST)
            if form.is_valid():
                form.save(commit=False)
                cur_question_number = form.cleaned_data.get('question_number')
                number_list = TextQuestion.objects.all().order_by('question_number').values_list(
                    'question_number').distinct()

                if len(number_list.filter(question_number=cur_question_number)) == 0:
                    res = ["There are groups:"]
                    for item in number_list:
                        res.append(f"Question number №{item[0]}")
                    form = CloseTextQuestionForm()
                    return render(request, 'main/for_from.html',
                                  {'form': form, 'list': res, 'tittle': "Get results for text question.",
                                   'message': "Question number doesn't exist"})
                else:
                    current_path = os.path.abspath(os.path.dirname(__name__))
                    current_path += "_results/"

                    users = ChatUser.objects.all()
                    for user in users:
                        questions = TextQuestion.objects.filter(user_id=user,
                                                                question_number=cur_question_number, is_closed=True). \
                            values_list('user_answer', 'user_image', 'question')

                        target_path = f"{user.student_id.group_id.group_number}/{user.student_id.last_name} {user.student_id.first_name}/"
                        directory = current_path + target_path

                        if not os.path.isdir(directory):
                            os.makedirs(directory)

                        for item in questions:
                            if item[0] != "":
                                with open(directory + f"{user.student_id.group_id.group_number}.{user.student_id.last_name}_{user.student_id.first_name}.txt", 'w') as file:
                                    answer = f"Question: {item[2]} \n Answer: {item[0]}\n"
                                    file.write(answer)

                            if item[1] != "":
                                image_dict = json.loads(item[1])
                                file_info = bot.get_file(image_dict['file_id'])
                                image = bot.download_file(file_info.file_path)
                                with open(directory + f"question_{cur_question_number}.png", 'wb') as file:
                                    file.write(image)

                    return render(request, 'main/results.html', {'list': ["The results will be saved in the django "
                                                                          "project folder."]})
        else:
            number_list = TextQuestion.objects.all().order_by('question_number').values_list(
                'question_number').distinct()
            res = ["There are groups:"]
            for item in number_list:
                res.append(f"Question number №{item[0]}")
            form = CloseTextQuestionForm()
        return render(request, 'main/for_from.html', {'form': form, 'tittle': "Get results for text question", 'list': res})
    return redirect('home')
