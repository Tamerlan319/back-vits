from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Group, Student, Teacher, PhoneConfirmation, UserPhone

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'phone_verified')
    list_filter = ('role', 'is_active', 'phone_verified', 'is_blocked')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональные данные', {
            'fields': ('last_name', 'first_name', 'middle_name', 'email', 'avatar')
        }),
        ('Статусы', {
            'fields': ('is_active', 'phone_verified', 'is_verified', 'is_blocked', 'role', 'verification_code')
        }),
        ('Блокировка', {
            'fields': ('blocked_at', 'blocked_reason', 'blocked_by')
        }),
        ('Права доступа', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

    actions = ['block_users', 'unblock_users']

    def block_users(self, request, queryset):
        for user in queryset:
            user.block("Blocked by admin", request.user)
    block_users.short_description = "Block selected users"

    def unblock_users(self, request, queryset):
        for user in queryset:
            user.unblock()
    unblock_users.short_description = "Unblock selected users"

@admin.register(PhoneConfirmation)
class PhoneConfirmationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('phone',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('students',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'group')
    search_fields = ('user__username', 'user__email', 'user__phone', 'group__name')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__email', 'user__phone')

admin.site.register(UserPhone)

admin.site.register(User, CustomUserAdmin)
