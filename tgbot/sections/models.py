from django.contrib.auth.models import User
from django.db import models


class Section(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    schedule = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.id}. {self.name}'


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    section = models.ManyToManyField(Section)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {", ".join([section.name for section in self.section.all()])}'


class TelegramUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return self.username
