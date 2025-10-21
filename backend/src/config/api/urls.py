
from django.urls import path, include

urlpatterns = [
    path('forms/', include('apps.forms.urls')),
    path('users/', include('apps.users.urls'))

]