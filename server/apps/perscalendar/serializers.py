from rest_framework import serializers
from .models import Event, UserEvent
from .cors.services import GroupService
from django.utils import timezone

class EventSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField(read_only=True)
    group_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    creator_name = serializers.SerializerMethodField(read_only=True)
    recurrence_rule = serializers.JSONField(required=False, allow_null=True)
    recurrence_end = serializers.DateTimeField(required=False, allow_null=True)
    participants = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'start_time', 'end_time',
            'event_type', 'group_id', 'group_name', 'is_recurring',
            'recurrence_rule', 'recurrence_end', 'creator_name',
            'participants', 'created_at'
        ]
        extra_kwargs = {
            'creator': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def get_group_name(self, obj):
        if not obj.group_id:
            return None
        group = GroupService.get_group(obj.group_id)
        return group.get('name') if group else None

    def get_creator_name(self, obj):
        return obj.creator.get_full_name() or obj.creator.username

    def get_participants(self, obj):
        if obj.event_type not in [Event.EventType.GROUP, Event.EventType.DEADLINE]:
            return []
        
        participants = []
        for user_event in obj.event_users.all().select_related('user'):
            participants.append({
                'id': user_event.user.id,
                'name': user_event.user.get_full_name(),
                'is_completed': user_event.is_completed,
                'completed_at': user_event.completed_at
            })
        return participants

    def validate(self, data):
        # Проверка времени
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError(
                "Время окончания должно быть позже времени начала."
            )

        # Проверка групповых событий
        if data.get('event_type') == Event.EventType.GROUP and not data.get('group_id'):
            raise serializers.ValidationError(
                "Групповые события должны быть привязаны к группе."
            )

        # Проверка повторяющихся событий
        if data.get('is_recurring', False):
            if not data.get('recurrence_rule'):
                raise serializers.ValidationError(
                    "Для повторяющегося события необходимо указать правило повторения."
                )
            
            try:
                freq = data['recurrence_rule'].get('freq')
                if freq not in dict(Event.RecurrenceFrequency.choices):
                    raise serializers.ValidationError(
                        f"Недопустимое значение частоты. Допустимые: {dict(Event.RecurrenceFrequency.choices)}"
                    )
            except (AttributeError, KeyError):
                raise serializers.ValidationError(
                    "Правило повторения должно содержать 'freq' и 'interval'"
                )

        return data

    def create(self, validated_data):
        # Извлекаем данные, которые не относятся к модели Event
        participants_data = validated_data.pop('participants', None)
        
        # Создаем событие
        event = Event.objects.create(
            creator=self.context['request'].user,
            **validated_data
        )
        
        # Обрабатываем участников (для групповых событий)
        if event.event_type in [Event.EventType.GROUP, Event.EventType.DEADLINE]:
            self._handle_participants(event, participants_data)
        
        return event

    def _handle_participants(self, event, participants_data):
        """Обрабатывает участников группового события"""
        if event.group_id:
            # Автоматически добавляем участников группы
            group_members = GroupService.get_group_members(event.group_id)
            for member_id in group_members:
                UserEvent.objects.get_or_create(
                    user_id=member_id,
                    event=event,
                    defaults={'is_completed': False}
                )
        
        # Дополнительная обработка, если переданы данные участников
        if participants_data:
            for participant in participants_data:
                user_id = participant.get('user_id')
                notes = participant.get('notes')
                
                if user_id:
                    UserEvent.objects.update_or_create(
                        user_id=user_id,
                        event=event,
                        defaults={
                            'notes': notes,
                            'is_completed': participant.get('is_completed', False)
                        }
                    )