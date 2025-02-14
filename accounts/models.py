from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('사용자명은 필수입니다')
        
        # AI code rewiew refactoring: 최소 길이 제한 추가
        if len(username) < 3:
            raise ValueError("사용자명은 3자 이상이어야합니다")
        
        if not password or len(password) < 8:
            raise ValueError("비밀번호는 8자 이상이어야합니다")

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractUser):
    username = models.CharField('사용자명', max_length=15, unique=True)

    # AI code rewiew refactoring: 최소 길이 제한 추가
    nickname = models.CharField('닉네임', max_length=30, unique=True, validators=[MinLengthValidator(8)])  

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.username 