
from django.urls import path, include

urlpatterns = [
    path('', include('apps.forms.urls')),
    path('', include('apps.categories.urls')),
    path('users/', include('apps.users.urls'))

]