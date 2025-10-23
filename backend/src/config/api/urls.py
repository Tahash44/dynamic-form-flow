
from django.urls import path, include

urlpatterns = [
    path('', include('apps.forms.urls')),
    path('users/', include('apps.users.urls'))

]