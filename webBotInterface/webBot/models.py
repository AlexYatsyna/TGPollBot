from django.db import models


class Group(models.Model):
    group_number = models.CharField(max_length=6)
    group_course = models.IntegerField()
    number_of_students = models.IntegerField()

    def __str__(self):
        return "Group {}".format(self.group_number)


class Student(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=30)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
    list_number = models.IntegerField()

    def __str__(self):
        return f"Student {self.first_name} {self.last_name}"


class RegistrationState(models.Model):
    tg_chat_id = models.IntegerField()
    registration_state = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.tg_chat_id}"


class ChatUser(models.Model):
    tg_chat_id = models.IntegerField()
    student_id = models.OneToOneField(Student, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student_id}"


class SimplePoll(models.Model):
    message_id = models.BigIntegerField()
    poll_id = models.IntegerField()
    question_group = models.IntegerField()
    question_number = models.IntegerField()
    question = models.CharField(max_length=255)
    options = models.TextField()  # JSON-serialized (text) version of your list
    correct_option = models.IntegerField()
    open_period = models.IntegerField(blank=True, default=604800)
    user_id = models.ForeignKey(ChatUser, on_delete=models.CASCADE)
    user_choice = models.IntegerField(blank=True, default=-1)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"Question from poll {self.question_group} number {self.question_number} for {self.user_id}"


class TextQuestion(models.Model):
    message_id = models.BigIntegerField()
    question = models.CharField(max_length=255)
    question_number = models.IntegerField()
    user_answer = models.CharField(max_length=255, default="empty", blank=True)
    user_image = models.TextField(default="empty", blank=True)  # JSON-serialized
    user_id = models.ForeignKey(ChatUser, on_delete=models.CASCADE)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"Question number {self.question_number} for {self.user_id}"
