from rest_framework import viewsets, permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from .models import Category, Tag, News, Comment, Like
from .serializers import (
    CategorySerializer, TagSerializer, NewsSerializer, 
    CommentSerializer, LikeSerializer
)
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'

class NewsCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'
    cursor_query_param = 'cursor'

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def handle_exception(self, exc):
        if isinstance(exc, ObjectDoesNotExist):
            exc = NotFound("Категория не найдена")
        return super().handle_exception(exc)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def handle_exception(self, exc):
        if isinstance(exc, ObjectDoesNotExist):
            exc = NotFound("Тег не найден")
        return super().handle_exception(exc)

class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = NewsCursorPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated or self.request.user.role != 'admin':
            queryset = queryset.filter(is_published=True)
        return queryset

    def perform_create(self, serializer):
        try:
            serializer.save(author=self.request.user)
        except Exception as e:
            raise ValidationError(str(e))
    
    @action(detail=False, methods=['get'])
    def latest_news(self, request):
        try:
            queryset = News.objects.filter(is_published=True).order_by('-created_at')[:3]
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            raise ValidationError(f"Ошибка при получении последних новостей: {str(e)}")

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        try:
            news = self.get_object()
            user = request.user
            
            if not user.is_authenticated:
                raise PermissionDenied("Требуется авторизация")
            
            like, created = Like.objects.get_or_create(news=news, user=user)
            
            if not created:
                like.delete()
                return Response({'status': 'Лайк удален'}, status=status.HTTP_204_NO_CONTENT)
            return Response({'status': 'Лайк добавлен'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise ValidationError(str(e))

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        try:
            news = self.get_object()
            comments = news.comments.filter(is_active=True)
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        except Exception as e:
            raise ValidationError(f"Ошибка при получении комментариев: {str(e)}")
    
    def handle_exception(self, exc):
        if isinstance(exc, ObjectDoesNotExist):
            exc = NotFound("Новость не найдена")
        return super().handle_exception(exc)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        try:
            news_id = self.request.data.get('news')
            if not news_id:
                raise ValidationError("Не указана новость для комментария")
                
            news = get_object_or_404(News, id=news_id)
            serializer.save(author=self.request.user, news=news)
        except Exception as e:
            raise ValidationError(str(e))
    
    def handle_exception(self, exc):
        if isinstance(exc, ObjectDoesNotExist):
            exc = NotFound("Комментарий не найден")
        return super().handle_exception(exc)

class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        try:
            news_id = self.request.data.get('news')
            if not news_id:
                raise ValidationError("Не указана новость для лайка")
                
            news = get_object_or_404(News, id=news_id)
            
            if Like.objects.filter(news=news, user=self.request.user).exists():
                raise ValidationError("Вы уже поставили лайк этой новости")
                
            serializer.save(user=self.request.user, news=news)
        except Exception as e:
            raise ValidationError(str(e))
    
    def handle_exception(self, exc):
        if isinstance(exc, ObjectDoesNotExist):
            exc = NotFound("Лайк не найден")
        return super().handle_exception(exc)