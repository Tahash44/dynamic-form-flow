from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import (
    ForgotPasswordView, 
    LoginView,
    RefreshTokenView,
    ResetPasswordView, 
    VerifyOTPView, 
    RegisterView,
    VerifyResetOTPView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh-token'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("verify-reset-otp/", VerifyResetOTPView.as_view(), name="verify-reset-otp"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]