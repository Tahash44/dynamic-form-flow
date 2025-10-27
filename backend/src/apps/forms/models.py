from django.contrib.auth.models import User
from django.db import models

class Form(models.Model):
    PUBLIC = 'public'
    PRIVATE = 'private'
    ACCESS_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private (password)'),
    ]

    access = models.CharField(max_length=10, choices=ACCESS_CHOICES, default=PUBLIC)
    password = models.CharField(max_length=64, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=8, unique=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.access == self.PRIVATE and not self.password.strip():
            raise ValidationError({'password': 'Password required for private forms.'})

    def save(self, *args, **kwargs):
        import secrets
        if not self.slug:
            self.slug = secrets.token_urlsafe(6)[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['access']),
            models.Index(fields=['slug']),
        ]

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

    class Meta:
        unique_together = ('form', 'position')
        ordering = ['position']

class Response(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

class Answer(models.Model):
    response = models.ForeignKey(Response, related_name='answers', on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    value = models.TextField()

    def __str__(self):
        return f'{self.field.question}: {self.value[:20]}'
