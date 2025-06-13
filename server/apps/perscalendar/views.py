from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, UserEvent
from .serializers import EventSerializer, EventSerializer
from .cors.permissions import EventPermission
from .cors.services import GroupService
from django.db.models import Q
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().select_related('creator')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]  # По умолчанию для изменяющих методов
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'group_id', 'creator', 'is_recurring']

    def get_permissions(self):
        # Разрешаем доступ без авторизации только для безопасных методов
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if not user.is_authenticated:
            return queryset.filter(event_type='global')

        if user.role == 'admin':
            return queryset.exclude(
                Q(event_type='personal') & ~Q(creator=user))
        
        elif user.role == 'teacher':
            return queryset.filter(
                Q(event_type='group') |
                Q(event_type='global') |
                Q(event_type='personal', creator=user))
        
        elif user.role == 'student':
            # Используем локальные группы
            user_groups = list(user.groups.values_list('id', flat=True))
            return queryset.filter(
                Q(event_type='group', group_id__in=user_groups) |
                Q(event_type='global') |
                Q(event_type='personal', creator=user))
        
        elif user.role == 'guest':
            return queryset.filter(event_type='global')
        
        return queryset.none()

    def perform_create(self, serializer):
        # Автоматически назначаем создателя события
        serializer.save()

    @action(detail=True, methods=['get'])
    def occurrences(self, request, pk=None):
        """Возвращает все вхождения повторяющегося события"""
        event = self.get_object()
        start = request.query_params.get('start')
        end = request.query_params.get('end')

        try:
            start = parser.parse(start) if start else None
            end = parser.parse(end) if end else None
        except ValueError:
            return Response(
                {"error": "Неверный формат даты. Используйте ISO формат."},
                status=status.HTTP_400_BAD_REQUEST
            )

        occurrences = event.get_occurrences(start, end)
        return Response(occurrences)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Отмечает событие как выполненное для текущего пользователя"""
        event = self.get_object()
        user = request.user
        
        user_event, created = UserEvent.objects.get_or_create(
            user=user,
            event=event,
            defaults={'is_completed': True}
        )
        
        if not created:
            user_event.is_completed = True
            user_event.save()
        
        return Response(
            UserEventSerializer(user_event).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Возвращает предстоящие события пользователя"""
        user = request.user
        now = timezone.now()
        
        # Личные события пользователя
        personal_events = Event.objects.filter(
            event_type='personal',
            creator=user,
            end_time__gte=now
        )
        
        # Групповые события из групп пользователя
        user_groups = GroupService.get_user_groups(user.id)
        group_events = Event.objects.filter(
            event_type='group',
            group_id__in=user_groups,
            end_time__gte=now
        )
        
        # Общие события
        global_events = Event.objects.filter(
            event_type='global',
            end_time__gte=now
        )
        
        # Объединяем все события
        events = (personal_events | group_events | global_events).distinct().order_by('start_time')
        
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)