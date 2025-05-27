from rest_framework import serializers
from .models import User, Group, PhoneVerification, PhoneConfirmation, Appeal, AppealResponse, Notification
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random
import phonenumbers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'phone', 'is_active']
        
class VKAuthSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    state = serializers.CharField(required=False)

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

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

class AppealSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appeal
        fields = '__all__'
        read_only_fields = ('user', 'status', 'created_at', 'updated_at')

class AppealResponseSerializer(serializers.ModelSerializer):
    admin = UserSerializer(read_only=True)
    
    class Meta:
        model = AppealResponse
        fields = '__all__'
        read_only_fields = ('admin', 'created_at')

class NotificationSerializer(serializers.ModelSerializer):
    appeal = AppealSerializer(read_only=True)
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('user', 'is_read', 'created_at')