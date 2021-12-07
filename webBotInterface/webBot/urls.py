from django.urls import path
from . import views
urlpatterns = [
    path('', views.main_page, name="home"),
    path('newTextQuestion', views.add_text_question, name="new_text_question"),
    path('closeTextQuestion', views.close_text_question, name="close_text_question"),
    path('closeSurvey', views.close_survey, name="close_survey"),
    path('sendPoll', views.send_poll, name="send_poll"),
    path('surveyResults', views.survey_results, name="survey_results"),
    path('histogram', views.get_histogram, name="histogram"),
    path('textResults', views.get_text_result, name="text_results"),
]