from django.contrib.auth.models import User
from django.db import models
from apps.forms.models import Form



# Create your models here.
class FormCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    forms = models.ManyToManyField(Form, related_name='categories')

    class Meta:
        unique_together = ('user', 'name')