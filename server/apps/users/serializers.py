from rest_framework import serializers
from .models import User, Group, PhoneVerification, PhoneConfirmation
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random
import phonenumbers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import User, UserActivityLog
from django.utils.translation import gettext_lazy as _

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
    phone = PhoneNumberField(region='RU')
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    middle_name = serializers.CharField(required=False)  # Добавляем отчество
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    
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

class AdminUserListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'uuid',
            'username',
            'full_name',
            'email',
            'phone',
            'role',
            'role_display',
            'is_active',
            'is_blocked',
            'date_joined',
            'last_login',
            'status'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_status(self, obj):
        if obj.is_blocked:
            return _("Blocked")
        return _("Active") if obj.is_active else _("Inactive")

class AdminUserDetailSerializer(serializers.ModelSerializer):
    activity_logs = serializers.SerializerMethodField()
    blocked_by = serializers.StringRelatedField()
    
    class Meta:
        model = User
        fields = [
            'uuid',
            'username',
            'first_name',
            'last_name',
            'middle_name',
            'email',
            'phone',
            'role',
            'is_active',
            'is_blocked',
            'blocked_at',
            'blocked_reason',
            'blocked_by',
            'date_joined',
            'last_login',
            'phone_verified',
            'is_verified',
            'activity_logs'
        ]
        read_only_fields = [
            'uuid',
            'date_joined',
            'last_login',
            'phone_verified',
            'is_verified',
            'activity_logs'
        ]
    
    def get_activity_logs(self, obj):
        from .models import UserActivityLog
        logs = UserActivityLog.objects.filter(user=obj).order_by('-created_at')[:10]
        return UserActivityLogSerializer(logs, many=True).data

class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'middle_name',
            'email',
            'role',
            'is_active',
            'is_blocked',
            'blocked_reason'
        ]
    
    def validate(self, data):
        request = self.context.get('request')
        
        # Проверка на блокировку
        if 'is_blocked' in data and data['is_blocked']:
            if not data.get('blocked_reason'):
                raise serializers.ValidationError(
                    _("Block reason is required when blocking a user")
                )
            if not request.user.has_perm('users.block_user'):
                raise serializers.ValidationError(
                    _("You don't have permission to block users")
                )
        
        # Проверка изменения роли
        if 'role' in data and data['role'] != self.instance.role:
            if not request.user.has_perm('users.change_role'):
                raise serializers.ValidationError(
                    _("You don't have permission to change user roles")
                )
        
        return data

class UserActivityLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = UserActivityLog
        fields = [
            'action',
            'action_display',
            'ip_address',
            'created_at',
            'metadata'
        ]

class UserSearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False)
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        required=False
    )
    is_active = serializers.BooleanField(required=False)
    is_blocked = serializers.BooleanField(required=False)
    date_joined_after = serializers.DateField(required=False)
    date_joined_before = serializers.DateField(required=False)