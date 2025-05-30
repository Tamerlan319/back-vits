from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField  # Импорт PhoneNumberField
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from datetime import timedelta
import uuid
from server.settings.environments.storage_backends import YandexMediaStorage

class PhoneConfirmation(models.Model):
    phone = PhoneNumberField(region='RU', unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    registration_data = models.JSONField()  # Будем хранить все данные регистрации
    
    def is_expired(self):
        return (timezone.now() - self.created_at) > timedelta(minutes=5)
    
    class Meta:
        verbose_name = "Подтверждение телефона"
        verbose_name_plural = "Подтверждения телефонов"
    
    def __str__(self):
        return f"Подтверждение для {str(self.phone)}"

class User(AbstractUser, PermissionsMixin):
    class Role(models.TextChoices):
        GUEST = 'guest', _('Гость')
        STUDENT = 'student', _('Студент')
        TEACHER = 'teacher', _('Преподаватель')
        ADMIN = 'admin', _('Администратор')
        MODERATOR = 'moderator', _('Модератор')

    # Основные поля
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    username = models.CharField(_('username'), max_length=150, unique=True)
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    phone = PhoneNumberField(_('phone number'), region='RU', unique=True, null=True, blank=True)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    
    # Персональные данные
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    middle_name = models.CharField(_('middle name'), max_length=150, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        storage=YandexMediaStorage(),
        null=True,
        blank=True
    )

    
    # Статусы
    is_active = models.BooleanField(_('active'), default=True)
    is_verified = models.BooleanField(_('verified'), default=False)
    is_blocked = models.BooleanField(_('blocked'), default=False)
    phone_verified = models.BooleanField(_('phone verified'), default=False)
    
    # Метаданные
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.GUEST
    )
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    
    # Блокировка
    blocked_at = models.DateTimeField(_('blocked at'), null=True, blank=True)
    blocked_reason = models.TextField(_('block reason'), blank=True, null=True)
    blocked_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blocked_users'
    )
    
    # Дополнительные поля
    vk_id = models.BigIntegerField(_('VK ID'), unique=True, null=True, blank=True)
    has_unread_notifications = models.BooleanField(_('has unread notifications'), default=False)
    
    # Настройки
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username', 'email']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
            models.Index(fields=['is_blocked']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone})" if self.phone else self.username
    
    def get_full_name(self):
        return ' '.join(filter(None, [self.last_name, self.first_name, self.middle_name]))
    
    def block(self, reason, blocked_by):
        self.is_blocked = True
        self.blocked_at = timezone.now()
        self.blocked_reason = reason
        self.blocked_by = blocked_by
        self.save(update_fields=['is_blocked', 'blocked_at', 'blocked_reason', 'blocked_by'])
    
    def unblock(self):
        self.is_blocked = False
        self.blocked_at = None
        self.blocked_reason = None
        self.blocked_by = None
        self.save(update_fields=['is_blocked', 'blocked_at', 'blocked_reason', 'blocked_by'])

class UserActivityLog(models.Model):
    class ActionType(models.TextChoices):
        LOGIN = 'login', _('Вход в систему')
        LOGOUT = 'logout', _('Выход из системы')
        PROFILE_UPDATE = 'profile_update', _('Обновление профиля')
        PASSWORD_CHANGE = 'password_change', _('Смена пароля')
        BLOCK = 'block', _('Блокировка')
        UNBLOCK = 'unblock', _('Разблокировка')
        ROLE_CHANGE = 'role_change', _('Изменение роли')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name=_('user')
    )
    action = models.CharField(
        _('action'),
        max_length=50,
        choices=ActionType.choices
    )
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True, null=True)
    metadata = models.JSONField(_('metadata'), default=dict)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('user activity log')
        verbose_name_plural = _('user activity logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} at {self.created_at}"

class PhoneVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_verifications')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        """Проверяет, действителен ли код"""
        return not self.is_used and \
               (timezone.now() - self.created_at < timedelta(minutes=5))

class Group(models.Model):
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(User, related_name='student_groups')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"

class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='teacher_profile'
    )

    def __str__(self):
        return self.user.get_full_name()

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"