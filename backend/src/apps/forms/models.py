from django.contrib.auth.models import User
from django.db import models

class Form(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=8, unique=True)

    def __str__(self):
        return self.name

class Field(models.Model):
    FIELD_TYPES = [
        ('text', 'متن'),
        ('select', 'گزینه‌ای'),
        ('checkbox', 'چک‌باکس'),
        ('number', 'عددی'),
        ('date', 'تاریخ'),
    ]

    form = models.ForeignKey(Form, related_name='fields', on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    position = models.IntegerField(default=0)
    options = models.JSONField(blank=True, null=True)
    max_length = models.IntegerField(blank=True, null=True)
    min_value = models.IntegerField(blank=True, null=True)
    max_value = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.question} ({self.field_type})"

class Response(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

class Answer(models.Model):
    response = models.ForeignKey(Response, related_name='answers', on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    value = models.TextField()
