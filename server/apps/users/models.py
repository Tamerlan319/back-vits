from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField  # Импорт PhoneNumberField
from django.utils import timezone
from datetime import timedelta

class PhoneConfirmation(models.Model):
    phone = PhoneNumberField(region='RU', unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)  # Оставляем только это определение
    registration_data = models.JSONField()  # Добавляем поле для хранения данных регистрации
    
    def is_expired(self):
        return (timezone.now() - self.created_at) > timedelta(minutes=5)
        
    class Meta:
        verbose_name = "Подтверждение телефона"
        verbose_name_plural = "Подтверждения телефонов"

    def __str__(self):
        return f"Подтверждение для {str(self.phone)}"  # Явное преобразование в строку

class User(AbstractUser, PermissionsMixin):
    last_name = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True, null=True)
    role = models.CharField(max_length=50, choices=[('guest', 'Гость'), ('student', 'Студент'), ('teacher', 'Преподаватель'), ('admin', 'Администратор')])
    groups = models.ManyToManyField('Group', related_name='custom_user_groups', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_permissions_set', blank=True)
    is_active = models.BooleanField(default=False)
    phone = PhoneNumberField(region='RU', null=True, blank=True)
    phone_verified = models.BooleanField(default=False, verbose_name="Телефон подтвержден")
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    code_sent_at = models.DateTimeField(null=True, blank=True)

    # Делаем username обязательным, но аутентификация будет по телефону
    USERNAME_FIELD = 'phone'  # Основное поле для аутентификации
    REQUIRED_FIELDS = ['username']  # Обязательные поля при создании superuser

    def save(self, *args, **kwargs):
        if self.role in ['guest', 'teacher', 'admin', 'student'] and self.groups.exists():
            raise ValidationError("Teachers and Admins cannot have groups.")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        # Преобразуем PhoneNumber в строку перед возвратом
        phone_str = str(self.phone) if self.phone else ''
        return f"{self.username} ({phone_str})"

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