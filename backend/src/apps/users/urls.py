from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView

from .views import RegisterView, LoginView, VerifyOTPView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
]