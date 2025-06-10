from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from .models import Category, Tag, News, Comment, Like, NewsImage
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

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
    
    def validate_name(self, value):
        if len(value) < 3:
            raise ValidationError("Название категории должно содержать минимум 3 символа")
        return value

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
    
    def validate_name(self, value):
        if len(value) < 2:
            raise ValidationError("Название тега должно содержать минимум 2 символа")
        return value

class TagRelatedField(serializers.RelatedField):
    def to_internal_value(self, data):
        if isinstance(data, int):
            try:
                return Tag.objects.get(pk=data)
            except Tag.DoesNotExist:
                raise ValidationError(f"Тег с ID {data} не существует")
        elif isinstance(data, str):
            tag, created = Tag.objects.get_or_create(name=data)
            return tag
        raise ValidationError("Тег должен быть ID (число) или названием (строка)")

    def to_representation(self, value):
        return TagSerializer(value).data

class CategoryRelatedField(serializers.RelatedField):
    def to_internal_value(self, data):
        if isinstance(data, int):
            try:
                return Category.objects.get(pk=data)
            except Category.DoesNotExist:
                raise ValidationError(f"Категория с ID {data} не существует")
        elif isinstance(data, str):
            category, created = Category.objects.get_or_create(
                name=data, 
            )
            return category
        raise ValidationError("Категория должна быть ID (число) или названием (строка)")

    def to_representation(self, value):
        return CategorySerializer(value).data

class NewsWriteSerializer(serializers.ModelSerializer):
    category = CategoryRelatedField(
        queryset=Category.objects.all(),
        required=True
    )
    tags = TagRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(
            max_length=100000,
            allow_empty_file=False,
            use_url=False,
            validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])]
        ),
        write_only=True,
        required=False
    )

    class Meta:
        model = News
        fields = [
            'title', 'content', 'category', 'tags',
            'is_published', 'uploaded_images'
        ]
        extra_kwargs = {
            'title': {'min_length': 5, 'max_length': 200},
            'content': {'min_length': 50}
        }

    def create(self, validated_data):
        # Удаляем author, если он случайно попал в данные
        validated_data.pop('author', None)
        
        uploaded_images = validated_data.pop('uploaded_images', [])
        tags = validated_data.pop('tags', [])
        category = validated_data.pop('category')
        
        # Создаём новость
        news = News.objects.create(
            author=self.context['request'].user,
            category=category,
            **validated_data
        )
        
        # Добавляем теги
        news.tags.set(tags)
        
        # Добавляем изображения (не более 6)
        for image in uploaded_images[:6]:
            NewsImage.objects.create(news=news, image=image)
            
        return news

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        tags = validated_data.pop('tags', None)
        category = validated_data.pop('category', None)
        
        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if category is not None:
            instance.category = category
        
        instance.save()
        
        # Обновляем теги если они переданы
        if tags is not None:
            instance.tags.set(tags)
        
        # Добавляем новые изображения (проверяем общее количество)
        existing_images_count = instance.images.count()
        remaining_slots = max(0, 6 - existing_images_count)
        
        for image in uploaded_images[:remaining_slots]:
            NewsImage.objects.create(news=instance, image=image)
            
        return instance

class NewsReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = NewsImageSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            'id', 'title', 'content', 'author', 'category', 'tags',
            'images', 'is_published', 'created_at', 'updated_at',
            'comments_count', 'likes_count'
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes_count(self, obj):
        return obj.likes.count()

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'news', 'author', 'text', 'created_at']
        extra_kwargs = {
            'text': {'min_length': 5, 'max_length': 1000}
        }

    def validate_text(self, value):
        if len(value.split()) < 3:
            raise ValidationError("Комментарий должен содержать минимум 3 слова")
        return value

class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'news', 'user', 'created_at']
    
    def validate(self, data):
        user = self.context['request'].user
        news = data['news']
        
        if Like.objects.filter(news=news, user=user).exists():
            raise ValidationError("Вы уже поставили лайк этой новости")
            
        return data