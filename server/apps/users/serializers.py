from rest_framework import serializers
from .models import User, Group, PhoneVerification, PhoneConfirmation
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random
import phonenumbers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'middle_name', 'role', 'groups')

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

# class RegisterSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
#     password2 = serializers.CharField(write_only=True, required=True)

#     class Meta:
#         model = User
#         fields = ('username', 'phone', 'first_name', 'last_name', 'password', 'password2')
#         extra_kwargs = {
#             'username': {'required': True},
#             'phone': {'required': True},
#         }

#     def validate_phone(self, value):
#         try:
#             parsed = phonenumbers.parse(str(value), None)
#             if not phonenumbers.is_valid_number(parsed):
#                 raise serializers.ValidationError("Неверный номер телефона")
#         except phonenumbers.NumberParseException:
#             raise serializers.ValidationError("Неверный формат номера телефона")
#         return value

#     def validate(self, attrs):
#         if attrs['password'] != attrs['password2']:
#             raise serializers.ValidationError({"password": "Пароли не совпадают."})
#         return attrs

#     def create(self, validated_data):
#         user = User.objects.create_user(
#             username=validated_data['username'],
#             phone=validated_data['phone'],
#             first_name=validated_data.get('first_name', ''),
#             last_name=validated_data.get('last_name', ''),
#             password=validated_data['password'],
#             is_active=True
#         )
#         return user

class RegisterInitSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    def validate_phone(self, value):
        try:
            parsed = phonenumbers.parse(value, 'RU')
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Неверный номер телефона")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Неверный формат номера")

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Это имя пользователя уже занято"})
        if User.objects.filter(phone=data['phone']).exists():
            raise serializers.ValidationError({"phone": "Этот телефон уже зарегистрирован"})
        return data

class RegisterConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            confirmation = PhoneConfirmation.objects.get(phone=data['phone'])
            if confirmation.is_expired():
                confirmation.delete()
                raise serializers.ValidationError("Срок действия кода истёк")
            if confirmation.code != data['code']:
                raise serializers.ValidationError("Неверный код подтверждения")
            data['confirmation'] = confirmation
        except PhoneConfirmation.DoesNotExist:
            raise serializers.ValidationError("Не найдена запись для подтверждения")
        return data

from django.contrib.auth import authenticate

class AuthorizationSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            phone=attrs['phone'],
            password=attrs['password']
        )
        
        if not user:
            raise serializers.ValidationError("Неверный номер телефона или пароль.")
        if not user.phone_verified:
            raise serializers.ValidationError("Телефон не подтвержден.")
        
        attrs['user'] = user
        return attrs

# class AuthorizationSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, attrs):
#         email = attrs.get('email')
#         password = attrs.get('password')

#         if email and password:
#             user = authenticate(request=self.context.get('request'), email=email, password=password)
#             if not user:
#                 raise serializers.ValidationError("Unable to log in with provided credentials.")
#         else:
#             raise serializers.ValidationError("Must include 'email' and 'password'.")

#         attrs['user'] = user
#         return attrs

class PhoneLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            phone=attrs['phone'],
            password=attrs['password']
        )
        
        if not user:
            raise serializers.ValidationError("Неверный номер телефона или пароль.")
        if not user.phone_verified:
            raise serializers.ValidationError("Телефон не подтвержден.")
        
        attrs['user'] = user
        return attrs

class PhoneVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    
    def validate(self, attrs):
        try:
            verification = PhoneVerification.objects.filter(
                user__phone=attrs['phone'],
                code=attrs['code'],
                is_used=False
            ).latest('created_at')
        except PhoneVerification.DoesNotExist:
            raise serializers.ValidationError("Неверный код подтверждения.")
        
        if not verification.is_valid():
            raise serializers.ValidationError("Срок действия кода истек.")
        
        attrs['verification'] = verification
        return attrs