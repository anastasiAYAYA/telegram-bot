from django.contrib import admin
from .models import Section, Enrollment, TelegramUser

# Register your models here.
admin.site.register(Section)
admin.site.register(Enrollment)
admin.site.register(TelegramUser)
