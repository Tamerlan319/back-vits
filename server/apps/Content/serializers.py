from rest_framework import serializers
from .models import Banner, Achievement, Review
from django.conf import settings

from rest_framework import serializers
from django.core.exceptions import ValidationError
import os

def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')

def validate_image_size(value):
    limit = 5 * 1024 * 1024  # 2MB
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 2 MB.')

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