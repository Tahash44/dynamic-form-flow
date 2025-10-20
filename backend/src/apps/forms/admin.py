from django.contrib import admin

from .models import form, static_pages

# Register your models here.
admin.site.register(form.Form)
admin.site.register(static_pages.WelcomePage)
admin.site.register(static_pages.FinalPage)
