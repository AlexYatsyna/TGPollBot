from django import forms
from .models import *


class TextQuestionForm(forms.ModelForm):
    class Meta:
        model = TextQuestion
        fields = ('question_number', 'question')


class CloseTextQuestionForm(forms.ModelForm):
    class Meta:
        model = TextQuestion
        fields = ('question_number',)


class CloseSurveyForm(forms.ModelForm):
    class Meta:
        model = SimplePoll
        fields = ('question_group',)


class SendPollForm(forms.ModelForm):
    option_0 = forms.CharField(max_length=40, required=True)
    option_1 = forms.CharField(max_length=40, required=True)
    option_2 = forms.CharField(max_length=40, required=True)
    option_3 = forms.CharField(max_length=40, required=True)
    option_4 = forms.CharField(max_length=40, required=True)

    class Meta:
        model = SimplePoll
        fields = ('question_group', 'question_number', 'question', 'correct_option', 'open_period')


class HistogramForm(forms.ModelForm):
    class Meta:
        model = SimplePoll
        fields = ('question_group', 'question_number',)
