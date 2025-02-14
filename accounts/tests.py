import pytest
import jwt
from datetime import datetime, timedelta, timezone
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError as DRFValidationError
from .serializers import SignupSerializer
from .views import AuthService, JWTManager

User = get_user_model()

# models 테스트
class TestUserModel(TestCase):
    def test_create_user_success(self):
        # 정상적인 유저 생성 테스트
        user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            nickname="testnick123"
        )
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.nickname, "testnick123")

    def test_create_user_no_username(self):
        # 사용자명 없이 생성 시도
        with self.assertRaises(ValueError):
            User.objects.create_user(username="", password="testpass123")

    def test_create_user_short_username(self):
        # 짧은 사용자명으로 생성 시도
        with self.assertRaises(ValueError):
            User.objects.create_user(username="ab", password="testpass123")

    def test_create_user_short_password(self):
        # 짧은 비밀번호로 생성 시도
        with self.assertRaises(ValueError):
            User.objects.create_user(username="testuser", password="short")

    def test_nickname_min_length(self):
        # 닉네임 최소 길이 제한 테스트
        user = User(
            username="testuser",
            password="testpass123",
            nickname="short"  # 8자 미만
        )
        with self.assertRaises(ValidationError):
            user.full_clean()

# serializers 테스트
class TestSignupSerializer(TestCase):
    def setUp(self):
        self.valid_user_data = {
            'username': 'testuser',
            'password': 'testpass123!@#',
            'password2': 'testpass123!@#',
            'nickname': 'testnickname123'
        }
        
    def test_valid_signup_data(self):
        # 유효한 데이터로 회원가입
        serializer = SignupSerializer(data=self.valid_user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, self.valid_user_data['username'])
        self.assertEqual(user.nickname, self.valid_user_data['nickname'])

    def test_passwords_not_match(self):
        # 비밀번호 불일치 테스트
        invalid_data = self.valid_user_data.copy()
        invalid_data['password2'] = 'differentpass123!@#'
        serializer = SignupSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_password_validation(self):
        # 너무 짧은 비밀번호 테스트
        invalid_data = self.valid_user_data.copy()
        invalid_data['password'] = 'short'
        invalid_data['password2'] = 'short'
        serializer = SignupSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_required_fields(self):
        # 필수 필드 누락 테스트
        invalid_data = {
            'username': 'testuser'
        }
        serializer = SignupSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        self.assertIn('password2', serializer.errors)
        self.assertIn('nickname', serializer.errors)

    def test_unique_username(self):
        # 중복된 username 테스트
        serializer1 = SignupSerializer(data=self.valid_user_data)
        self.assertTrue(serializer1.is_valid())
        serializer1.save()

        serializer2 = SignupSerializer(data=self.valid_user_data)
        self.assertFalse(serializer2.is_valid())
        self.assertIn('username', serializer2.errors)

# views 테스트
class TestAuthService(TestCase):
    def setUp(self):
        self.valid_user_data = {
            'username': 'testuser',
            'password': 'testpass123!@#',
            'password2': 'testpass123!@#',
            'nickname': 'testnickname123'
        }
        
    def test_signup_service_success(self):
        # AuthService 회원가입 성공 테스트
        user = AuthService.signup(self.valid_user_data)
        self.assertEqual(user.username, self.valid_user_data['username'])
        self.assertEqual(user.nickname, self.valid_user_data['nickname'])

    def test_signup_service_invalid_data(self):
        # AuthService 회원가입 실패 테스트
        invalid_data = self.valid_user_data.copy()
        invalid_data['password2'] = 'different'
        with self.assertRaises(ValueError):
            AuthService.signup(invalid_data)

    def test_login_service_success(self):
        # AuthService 로그인 성공 테스트
        AuthService.signup(self.valid_user_data)
        token_data = AuthService.login(
            username=self.valid_user_data['username'],
            password=self.valid_user_data['password']
        )
        self.assertIn('token', token_data)
        self.assertIsInstance(token_data['token'], str)

    def test_login_service_invalid_credentials(self):
        # AuthService 로그인 실패 테스트
        with self.assertRaises(ValueError):
            AuthService.login(username='wrong', password='wrong')

class TestAuthViews(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_user_data = {
            'username': 'testuser',
            'password': 'testpass123!@#',
            'password2': 'testpass123!@#',
            'nickname': 'testnickname123'
        }

    def test_signup_view_success(self):
        # 회원가입 API 성공 테스트
        response = self.client.post(reverse('accounts:signup'), self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], self.valid_user_data['username'])
        self.assertEqual(response.data['nickname'], self.valid_user_data['nickname'])
        self.assertEqual(response.data['roles'], [{"role": "USER"}])

    def test_signup_view_invalid_data(self):
        # 회원가입 API 실패 테스트
        invalid_data = self.valid_user_data.copy()
        invalid_data['password2'] = 'different'
        response = self.client.post(reverse('accounts:signup'), invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_view_success(self):
        # 로그인 API 성공 테스트
        self.client.post(reverse('accounts:signup'), self.valid_user_data)
        login_data = {
            'username': self.valid_user_data['username'],
            'password': self.valid_user_data['password']
        }
        response = self.client.post(reverse('accounts:login'), login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_view_invalid_credentials(self):
        # 로그인 API 실패 테스트
        login_data = {
            'username': 'wrong',
            'password': 'wrong'
        }
        response = self.client.post(reverse('accounts:login'), login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

# JWT 토큰 테스트
class TestJWTEndpoints(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'password': 'testpass123!@#',
            'password2': 'testpass123!@#',
            'nickname': 'testnickname123'
        }
        # 사용자 생성
        self.client.post(reverse('accounts:signup'), self.user_data)

    def test_token_obtain(self):
        # 토큰 발급 테스트
        response = self.client.post(reverse('accounts:token_obtain_pair'), {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        # 토큰 갱신 테스트
        token_response = self.client.post(reverse('accounts:token_obtain_pair'), {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        refresh_token = token_response.data['refresh']
        
        response = self.client.post(reverse('accounts:token_refresh'), {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_blacklist(self):
        # 토큰 블랙리스트 테스트
        token_response = self.client.post(reverse('accounts:token_obtain_pair'), {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        refresh_token = token_response.data['refresh']
        
        response = self.client.post(reverse('accounts:token_blacklist'), {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)