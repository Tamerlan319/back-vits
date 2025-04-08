from rest_framework import viewsets, permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Category, Tag, News, Comment, Like
from .serializers import (
    CategorySerializer, TagSerializer, NewsSerializer, 
    CommentSerializer, LikeSerializer
)
from django.shortcuts import get_object_or_404

class NewsCursorPagination(CursorPagination):
    page_size = 10  # Количество новостей на странице
    ordering = '-created_at'  # Обязательное поле для сортировки
    cursor_query_param = 'cursor'  # Параметр в URL (по умолчанию 'cursor')

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = NewsCursorPagination  # Используем курсорную пагинацию

    @action(detail=False, methods=['get'])
    def latest_news(self, request):
        """3 последние новости для главной страницы (без пагинации)"""
        queryset = News.objects.filter(is_published=True).order_by('-created_at')[:3]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        news = self.get_object()
        user = request.user
        like, created = Like.objects.get_or_create(news=news, user=user)
        if not created:
            like.delete()
            return Response({'status': 'Лайк удален'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'Лайк добавлен'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        news = self.get_object()
        comments = news.comments.filter(is_active=True)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        news = get_object_or_404(News, id=self.request.data.get('news'))
        serializer.save(author=self.request.user, news=news)

class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        news = get_object_or_404(News, id=self.request.data.get('news'))
        serializer.save(user=self.request.user, news=news)