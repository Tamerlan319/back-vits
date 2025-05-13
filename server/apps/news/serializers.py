from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
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

class NewsSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    images = NewsImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False, 
            use_url=False,
            validators=[
                FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
            ]
        ),
        write_only=True,
        required=False
    )

    class Meta:
        model = News
        fields = [
            'id', 'title', 'content', 'images', 'uploaded_images', 'created_at', 'updated_at',
            'is_published', 'author', 'category', 'tags', 'comments_count', 'likes_count'
        ]
        extra_kwargs = {
            'title': {'min_length': 5, 'max_length': 200},
            'content': {'min_length': 50}
        }

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def validate(self, data):
        # Проверка, что новость имеет хотя бы один тег
        if 'tags' in data and not data['tags']:
            raise ValidationError("Новость должна содержать хотя бы один тег")
        
        # Проверка, что загружено не более 5 изображений
        if 'uploaded_images' in data and len(data['uploaded_images']) > 5:
            raise ValidationError("Можно загрузить не более 5 изображений")
            
        return data

    def create(self, validated_data):
        try:
            uploaded_images = validated_data.pop('uploaded_images', [])
            tags_data = validated_data.pop('tags')
            category_data = validated_data.pop('category')
            
            news = News.objects.create(**validated_data, category=category_data)
            news.tags.set(tags_data)
            
            for image_data in uploaded_images:
                NewsImage.objects.create(news=news, image=image_data)
                
            return news
        except Exception as e:
            raise ValidationError(f"Ошибка при создании новости: {str(e)}")


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