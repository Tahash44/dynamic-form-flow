from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from .serializers import ForgotPasswordSerializer, LoginSerializer, ProfileSerializer, RefreshTokenSerializer, RegisterSerializer, ResetPasswordSerializer, VerifyOTPSerializer, VerifyResetOTPSerializer

import random

from .models import Profile

User = get_user_model()


class RegisterView(CreateAPIView):
    queryset = User
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)

        if not user:
            return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)

        otp = random.randint(100000, 999999)

        cache.set(f'otp_{username}', otp, 300)

        send_mail(
            subject='Your Login OTP',
            message=f'Hello {user.username},\n\nYour OTP for login is {otp}. It expires in 5 minutes.\n\nBest,\nDjango Form Flow',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )

        return Response({"meesage": 'OTP sent to your mail'}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        otp = serializer.validated_data['otp']

        cached_otp = cache.get(f'otp_{username}')
        if not cached_otp:
            return Response({'error': 'OTP expired or invalid'}, status=status.HTTP_400_BAD_REQUEST)
        
        if str(otp) != str(cached_otp):
            return Response({'error': 'Incorred OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        cache.delete(f'otp_{username}')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        refresh = RefreshToken.for_user(user)

        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_200_OK)
    

class ForgotPasswordView(APIView):
    """
    Step 1: User requests password reset -> send OTP via email
    """
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "No account found with this email."}, status=404)

        otp = random.randint(100000, 999999)
        cache.set(f"reset_otp_{email}", otp, timeout=300)  # 5 minutes

        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP for password reset is {otp}. It expires in 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"message": "OTP sent to your email."}, status=200)


class VerifyResetOTPView(APIView):
    """
    Step 2: Verify OTP (optional step, if you want to confirm before reset)
    """
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = VerifyResetOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        cached_otp = cache.get(f"reset_otp_{email}")
        if not cached_otp:
            return Response({"error": "OTP expired or invalid."}, status=400)

        if str(cached_otp) != str(otp):
            return Response({"error": "Incorrect OTP."}, status=400)

        return Response({"message": "OTP verified successfully."}, status=200)


class ResetPasswordView(APIView):
    """
    Step 3: Reset password after verifying OTP
    """
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        cached_otp = cache.get(f"reset_otp_{email}")
        if not cached_otp:
            return Response({"error": "OTP expired or invalid."}, status=400)

        if str(cached_otp) != str(otp):
            return Response({"error": "Incorrect OTP."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        user.set_password(new_password)
        user.save()

        cache.delete(f"reset_otp_{email}")

        return Response({"message": "Password reset successful."}, status=200)


class RefreshTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        seriazlier = RefreshTokenSerializer(data=request.data)
        seriazlier.is_valid(raise_exception=True)

        refresh_token = seriazlier.validated_data['refresh']
        try:
            old_token = RefreshToken(refresh_token)
            access_token = str(old_token.access_token)
            new_refresh = RefreshToken.for_user(request.user)
            return Response({
                'refresh': str(new_refresh),
                'access': access_token
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh']

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout Successfully.'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ProfileDetailView(RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
