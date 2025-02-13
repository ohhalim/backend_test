from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import SignupSerializer
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

import jwt
from datetime import datetime, timedelta


User = get_user_model()

@api_view(['POST'])
@authentication_classes([])      # 전역 인증 설정 무시
@permission_classes([AllowAny])  # 전역 IsAuthenticated 설정 무시
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "username": user.username,
            "nickname": user.nickname,
            "roles": [
                {
                    "role": "USER"
                }
            ]
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([])      # 전역 인증 설정 무시
@permission_classes([AllowAny])  # 전역 IsAuthenticated 설정 무시
def login(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')

        # 사용자 인증
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
            
        else:
            return Response({
                'error': '사용자명 또는 비밀번호가 올바르지 않습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)



class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, payload: dict, expires_delta: timedelta = None) -> str:
        """토큰 생성 메소드"""
        to_encode = payload.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)  # 기본 30분
            
        to_encode.update({"exp": expire})
        
        return jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )

    def verify_token(self, token: str) -> dict:
        """토큰 검증 메소드"""
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm]
        )