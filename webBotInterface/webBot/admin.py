from django.contrib import admin
from .models import *

admin.site.register(Group)
admin.site.register(Student)
admin.site.register(SimplePoll)
admin.site.register(ChatUser)
admin.site.register(TextQuestion)
admin.site.register(RegistrationState)
