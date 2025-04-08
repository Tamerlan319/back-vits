from django.db import models
from rest_framework import viewsets
from .models import Event
from .serializers import EventSerializer
from .cors.permissions import EventPermission
from django_filters.rest_framework import DjangoFilterBackend

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().select_related('creator')
    serializer_class = EventSerializer
    permission_classes = [EventPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'group_id']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.role == 'admin':
            # Админ: все события, кроме чужих личных
            return queryset.exclude(
                models.Q(event_type='personal') & ~models.Q(creator=user)
            )
        
        elif user.role == 'teacher':
            # Преподаватель: групповые, общие и свои личные
            return queryset.filter(
                models.Q(event_type='group') |
                models.Q(event_type='global') |
                models.Q(event_type='personal', creator=user)
            )
        
        elif user.role == 'student':
            # Студент: групповые его группы, общие и его личные
            return queryset.filter(
                models.Q(event_type='group', group_id__in=user.student_groups.values_list('id', flat=True)) |
                models.Q(event_type='global') |
                models.Q(event_type='personal', creator=user)
            )
        
        elif user.role == 'guest':
            # Гость: только общие события
            return queryset.filter(event_type='global')
        
        return queryset.none()

    def perform_create(self, serializer):
        # Автоматически назначаем создателя события
        serializer.save(creator=self.request.user)