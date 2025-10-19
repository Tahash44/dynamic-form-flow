from django.db import models

from config.settings import AUTH_USER_MODEL


class Form(models.Model):
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=False)
    slug = models.SlugField(max_length=8, unique=True)
