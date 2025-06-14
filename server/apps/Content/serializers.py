from rest_framework import serializers
from .models import Banner, Achievement, Review, OrganizationDocument, VideoContent
from django.conf import settings

from rest_framework import serializers
from django.core.exceptions import ValidationError
import os

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Неподдерживаемый тип файла.')

def validate_file_size(value):
    limit = 5 * 1024 * 1024  # 10MB
    if value.size > limit:
        raise ValidationError('Файл слишком большой. Максимальный размер - 10 МБ.')

def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Неподдерживаемый тип изображения.')

def validate_image_size(value):
    limit = 5 * 1024 * 1024  # 5MB
    if value.size > limit:
        raise ValidationError('Изображение слишком большое. Максимальный размер - 5 МБ.')

class BannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    image = serializers.ImageField(
        validators=[validate_image_extension, validate_image_size],
        write_only=True,
        required=True
    )

    class Meta:
        model = Banner
        fields = ['id', 'image', 'image_url', 'created_at', 'order']
        read_only_fields = ['image_url', 'created_at']
        extra_kwargs = {
            'image': {'write_only': True}
        }

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class AchievementSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    image = serializers.ImageField(
        validators=[validate_image_extension, validate_image_size],
        write_only=True,
        required=True
    )

    class Meta:
        model = Achievement
        fields = ['id', 'title', 'image', 'image_url', 'created_at']
        read_only_fields = ['image_url', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class ReviewSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    image = serializers.ImageField(
        validators=[validate_image_extension, validate_image_size],
        write_only=True,
        required=True
    )

    class Meta:
        model = Review
        fields = ['id', 'author', 'course', 'text', 'image', 'image_url', 'created_at']
        read_only_fields = ['created_at', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class OrganizationDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file = serializers.FileField(
        validators=[validate_file_extension, validate_file_size],
        write_only=True,
        required=True
    )

    class Meta:
        model = OrganizationDocument
        fields = ['id', 'title', 'file', 'file_url']
        read_only_fields = ['file_url']

    def get_file_url(self, obj):
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None

class VideoContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoContent
        fields = ['id', 'title', 'file', 'description']
        read_only_fields = []