from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from backend.src.apps.users.serializers import LoginSerializer, RegisterSerializer, VerifyOTPSerializer

import random


User = get_user_model()


class RegisterView(CreateAPIView):
    queryset = User
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
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
            message=f'Hello {user.username},\n\nYour OTP for login is {otp}. It expires in 5 minutes.\n\nBest,\nYour App Team',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )

        return Response({"meesage": 'OTP sent to your mail'}, status=status.HTTP_200_OK)
    
class VerifyOTPView(APIView):
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
    



