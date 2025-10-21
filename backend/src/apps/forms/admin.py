from django.contrib import admin
from django.db.models.base import Model

from .models import *

# Register your models here.
admin.site.register(Form)
admin.site.register(WelcomePage)
admin.site.register(FinalPage)
#Fields Type
admin.site.register(FormCheckBoxField)
admin.site.register(FormSelectField)
admin.site.register(FormTextField)
admin.site.register(FormNumberField)
admin.site.register(FormDateField)
