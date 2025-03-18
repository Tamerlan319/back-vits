from django.contrib import admin
from .models import User, Group, Student, Teacher
from django.contrib.auth.admin import UserAdmin

admin.site.register(User, UserAdmin)
admin.site.register(Group)
admin.site.register(Student)
admin.site.register(Teacher)