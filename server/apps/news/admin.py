from django.contrib import admin
from .models import Category, Tag, News, Comment, Like

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(News)
admin.site.register(Comment)
admin.site.register(Like)