from config.settings import AUTH_USER_MODEL
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator

class Form(models.Model):
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=False)
    slug = models.SlugField(max_length=8, unique=True)




class WelcomePage(models.Model):
    title = models.CharField(max_length=255)
    form = models.OneToOneField(Form, on_delete=models.CASCADE)
    description = models.TextField()
    entrance_button_text = models.CharField(max_length=50, blank=True)


class FinalPage(models.Model):
    text = models.TextField(null=False)
    form = models.OneToOneField(Form, on_delete=models.CASCADE)





class Field(models.Model):
    form = models.ForeignKey('Form', on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=0)
    question = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    required = models.BooleanField(null=False, default=False)
    show_position = models.BooleanField(null=False, default=True)

    class Meta:
        ordering = ['position']
        unique_together = ('form', 'position',)


def validate_string_list(value):
    """Validate that the value is a list of strings"""
    if not isinstance(value, list):
        raise ValidationError('Value must be a list')

    for item in value:
        if not isinstance(item, str):
            raise ValidationError('All items must be strings')


class CheckBoxField(Field):
    check_box_names = models.JSONField(
        default=list,
        validators=[validate_string_list],
    )
    minimum = models.PositiveSmallIntegerField(default=0)
    maximum = models.PositiveSmallIntegerField(
        null=True,
        validators=[MinValueValidator(1)],
    )


class SelectField(Field):
    options = models.JSONField(
        default=list,
        validators=[validate_string_list],
    )


class TextField(Field):
    max_length = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
