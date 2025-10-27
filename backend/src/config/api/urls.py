
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', include('apps.forms.urls')),
    path('users/', include('apps.users.urls')),
    path('processes/', include('apps.processes.urls')),
    path('categories/', include('apps.categories.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]