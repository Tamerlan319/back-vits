from rest_framework import viewsets, permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from .models import Category, Tag, News, Comment, Like
from .serializers import (
    CategorySerializer, TagSerializer, NewsReadSerializer, NewsWriteSerializer,
    CommentSerializer, LikeSerializer
)
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Кастомное разрешение:
    - Чтение разрешено всем
    - Создание/редактирование только администраторам
    """
    def has_permission(self, request, view):
        # Разрешаем GET, HEAD, OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # POST, PUT, PATCH, DELETE только для админов
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
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = NewsCursorPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return NewsWriteSerializer
        return NewsReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated or self.request.user.role != 'admin':
            queryset = queryset.filter(is_published=True)
        return queryset.select_related('author', 'category').prefetch_related('tags', 'images')

    def perform_create(self, serializer):
        try:
            instance = serializer.save(author=self.request.user)

            # # Отправка WebSocket уведомления
            # channel_layer = get_channel_layer()
            # async_to_sync(channel_layer.group_send)(
            #     'news_updates',
            #     {
            #         'type': 'news_update',
            #         'event': 'NEWS_CREATED',
            #         'data': NewsReadSerializer(instance).data
            #     }
            # )
        except Exception as e:
            raise ValidationError(str(e))

    def perform_update(self, serializer):
        try:
            instance = serializer.save()

            # Отправка WebSocket уведомления
            # channel_layer = get_channel_layer()
            # async_to_sync(channel_layer.group_send)(
            #     'news_updates',
            #     {
            #         'type': 'news_update',
            #         'event': 'NEWS_UPDATED',
            #         'data': NewsReadSerializer(instance).data
            #     }
            # )
        except Exception as e:
            raise ValidationError(str(e))

    def perform_destroy(self, instance):
        try:
            news_id = instance.id
            instance.delete()

            # Отправка WebSocket уведомления
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'news_updates',
                {
                    'type': 'news_update',
                    'event': 'NEWS_DELETED',
                    'data': {'id': news_id}
                }
            )
        except Exception as e:
            raise ValidationError(str(e))

    @action(detail=False, methods=['get'])
    def latest_news(self, request):
        try:
            queryset = News.objects.filter(is_published=True).order_by('-created_at')[:3]
            serializer = self.get_serializer(queryset, many=True)

            # # Отправляем обновление через WebSocket
            # channel_layer = get_channel_layer()
            # async_to_sync(channel_layer.group_send)(
            #     'news_updates',
            #     {
            #         'type': 'news_update',
            #         'event': 'LATEST_NEWS',
            #         'data': serializer.data
            #     }
            # )

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
            instance = serializer.save(author=self.request.user, news=news)

            # # Отправляем обновление через WebSocket
            # channel_layer = get_channel_layer()
            # async_to_sync(channel_layer.group_send)(
            #     f'news_{news_id}_comments',
            #     {
            #         'type': 'comment_update',
            #         'event': 'NEW_COMMENT',
            #         'data': CommentSerializer(instance).data
            #     }
            # )

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