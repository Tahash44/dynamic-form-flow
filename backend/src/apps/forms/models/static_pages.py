from django.db import models

from .form import Form


class WelcomePage(models.Model):
    title = models.CharField(max_length=255)
    form = models.OneToOneField(Form, on_delete=models.CASCADE)
    description = models.TextField()
    entrance_button_text = models.CharField(max_length=50, blank=True)


class FinalPage(models.Model):
    text = models.TextField(null=False)
    form = models.OneToOneField(Form, on_delete=models.CASCADE)
