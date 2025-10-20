from django.urls import path, include

urlpatterns = [
    path('forms/', include('apps.forms.urls')),
]