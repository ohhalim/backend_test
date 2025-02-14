from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


User = get_user_model()

# class SignupSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

#     # AI code rewiew refactoring: 비밀번호 2차 확인 추가
#     password2 = serializers.CharField(write_only=True, required=True)

#     class Meta:
#         model = User
#         fields = ('username', 'password', 'password2', 'nickname')  # password2를 따옴표로 감쌌습니다
    
#     # AI code rewiew refactoring: 비밀번호 2차 확인 추가 및 에러 상세 메세지 추가
#     def validate(self, data):
#         if data['password'] != data['password2']:
#             raise serializers.ValidationError({
#                 "password": "비밀번호가 일치하지 않습니다."
#             })
#         return data
    
#     # AI code rewiew refactoring: 비밀번호 2차 확인 추가
#     def create(self, validated_data):
#         validated_data.pop('password2')  # password2 제거
#         return User.objects.create_user(**validated_data)


# refactoring_unit_test로 바꾼 코드 
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'nickname')

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("비밀번호는 8자 이상이어야 합니다.")
        validate_password(value)
        return value
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                "password": "비밀번호가 일치하지 않습니다."
            })
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)