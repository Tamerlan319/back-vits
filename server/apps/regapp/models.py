from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    last_name = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=[('guest', 'Гость'), ('student', 'Студент'), ('teacher', 'Преподаватель'), ('admin', 'Администратор')])
    groups = models.ManyToManyField('Group', related_name='custom_user_groups', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_permissions_set', blank=True)

    def save(self, *args, **kwargs):
        if self.role in ['teacher', 'admin', 'student'] and self.groups.exists():
            raise ValidationError("Teachers and Admins cannot have groups.")
        super().save(*args, **kwargs)


class Group(models.Model):
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(User, related_name='student_groups')

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

class CalendarEvent(models.Model):
    description = models.TextField()
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_global = models.BooleanField(default=False)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

class Name(models.Model):
    text = models.CharField(max_length=255)

class Photo(models.Model):
    description = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    name = models.ForeignKey(Name, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)