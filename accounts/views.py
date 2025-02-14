from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import SignupSerializer
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken


import jwt
from datetime import datetime, timedelta

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


User = get_user_model()

class AuthService:
    @staticmethod
    def signup(data: dict) -> User:
        serializer = SignupSerializer(data=data)
        if serializer.is_valid():
            return serializer.save()
        raise ValueError(serializer.errors)

    @staticmethod
    def login(username: str, password: str) -> dict:
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValueError('사용자명 또는 비밀번호가 올바르지 않습니다.')
        refresh = RefreshToken.for_user(user)
        return {'token': str(refresh.access_token)}


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password', 'nickname'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
            'nickname': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'nickname': openapi.Schema(type=openapi.TYPE_STRING),
                'roles': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'role': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                )
            }
        )
    }
)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def signup(request):
    try:
        user = AuthService.signup(request.data)
        return Response({
            "username": user.username,
            "nickname": user.nickname,
            "roles": [{"role": "USER"}]
        }, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response(e.args[0], status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    }
)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    try:
        token_data = AuthService.login(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        return Response(token_data, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# simplejwt로 했는데 이걸 넣어야하나..?
# class JWTManager:
#     def __init__(self, secret_key: str, algorithm: str = "HS256"):
#         self.secret_key = secret_key
#         self.algorithm = algorithm

#     def create_token(self, payload: dict, expires_delta: timedelta = None) -> str:
#         """토큰 생성 메소드"""
#         to_encode = payload.copy()
        
#         if expires_delta:
#             expire = datetime.utcnow() + expires_delta
#         else:
#             expire = datetime.utcnow() + timedelta(minutes=30)  # 기본 30분
            
#         to_encode.update({"exp": expire})
        
#         return jwt.encode(
#             to_encode,
#             self.secret_key,
#             algorithm=self.algorithm
#         )

#     def verify_token(self, token: str) -> dict:
#         """토큰 검증 메소드"""
#         return jwt.decode(
#             token,
#             self.secret_key,
#             algorithms=[self.algorithm]
#         )