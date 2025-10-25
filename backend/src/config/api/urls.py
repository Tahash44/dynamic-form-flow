
from django.urls import path, include

urlpatterns = [
    path('', include('apps.forms.urls')),
    path('users/', include('apps.users.urls')),
    path('processes/', include('apps.processes.urls')),

]