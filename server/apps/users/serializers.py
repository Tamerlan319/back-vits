from rest_framework import serializers
from .models import User, Group, PhoneVerification
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'middle_name', 'role', 'groups')

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'middle_name', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            middle_name=validated_data['middle_name'],
            is_active=False  # Пользователь неактивен до подтверждения почты
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

from django.contrib.auth import authenticate

class AuthorizationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")

        attrs['user'] = user
        return attrs

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