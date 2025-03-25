from rest_framework import serializers
from .models import Category, Tag, News, Comment, Like, NewsImage
from django.contrib.auth import get_user_model

User = get_user_model()

class NewsImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsImage
        fields = ['id', 'image']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class NewsSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    images = NewsImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True
    )

    class Meta:
        model = News
        fields = [
            'id', 'title', 'content', 'images', 'uploaded_images', 'created_at', 'updated_at',
            'is_published', 'author', 'category', 'tags', 'comments_count', 'likes_count'
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images')
        tags_data = validated_data.pop('tags')
        category_data = validated_data.pop('category')
        news = News.objects.create(**validated_data, category=category_data)
        news.tags.set(tags_data)
        for image_data in uploaded_images:
            NewsImage.objects.create(news=news, image=image_data)
        return news


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'news', 'author', 'text', 'created_at', 'is_active']

class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'news', 'user', 'created_at']