from django.contrib import admin
from .models import User, Group, Student, Teacher, PhoneVerification
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    # Добавляем телефон в список отображаемых полей
    list_display = ('username', 'email', 'phone', 'role', 'is_active')
    
    # Полная переопределение fieldsets для добавления всех кастомных полей
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональные данные', {
            'fields': ('last_name', 'first_name', 'middle_name', 'email', 'phone')
        }),
        ('Статусы', {
            'fields': ('is_active', 'phone_verified', 'role', 'verification_code')
        }),
        ('Права доступа', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Поля при создании пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2', 'role'),
        }),
    )

# Исправленная регистрация - передаём только модель и кастомный админ-класс
admin.site.register(User, CustomUserAdmin)  # Только 2 аргумента!
admin.site.register(PhoneVerification)
admin.site.register(Group)
admin.site.register(Student)
admin.site.register(Teacher)