from django.db import models
from django.core.exceptions import ValidationError
from server.apps.users.models import User, Group

class Event(models.Model):
    class EventType(models.TextChoices):
        PERSONAL = 'personal', 'Личное'
        GROUP = 'group', 'Групповое'
        GLOBAL = 'global', 'Общее'
        DEADLINE = 'deadline', 'Дедлайн'

    class RecurrenceFrequency(models.TextChoices):
        DAILY = 'DAILY', 'Ежедневно'
        WEEKLY = 'WEEKLY', 'Еженедельно'
        MONTHLY = 'MONTHLY', 'Ежемесячно'
        YEARLY = 'YEARLY', 'Ежегодно'

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    start_time = models.DateTimeField(verbose_name="Время начала")
    end_time = models.DateTimeField(verbose_name="Время окончания")
    event_type = models.CharField(
        max_length=10, 
        choices=EventType.choices, 
        default=EventType.PERSONAL,
        verbose_name="Тип события"
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_events',
        verbose_name="Создатель"
    )
    group_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID группы")
    is_recurring = models.BooleanField(default=False, verbose_name="Повторяющееся")
    recurrence_rule = models.JSONField(blank=True, null=True, verbose_name="Правило повторения")
    recurrence_end = models.DateTimeField(blank=True, null=True, verbose_name="Окончание повторений")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"

    def clean(self):
        # Валидация времени
        if self.start_time >= self.end_time:
            raise ValidationError("Время окончания должно быть позже времени начала.")
        
        # Валидация групповых событий
        if self.event_type == self.EventType.GROUP and not self.group_id:
            raise ValidationError("Групповые события должны быть привязаны к группе.")
        
        # Валидация повторяющихся событий
        if self.is_recurring:
            if not self.recurrence_rule:
                raise ValidationError("Для повторяющегося события необходимо указать правило повторения.")
            try:
                self.validate_recurrence_rule()
            except ValueError as e:
                raise ValidationError(str(e))

    def validate_recurrence_rule(self):
        """Проверяет корректность правила повторения"""
        required_fields = ['freq', 'interval']
        if not all(field in self.recurrence_rule for field in required_fields):
            raise ValueError("Правило повторения должно содержать 'freq' и 'interval'")
        
        if self.recurrence_rule['freq'] not in dict(self.RecurrenceFrequency.choices):
            raise ValueError(f"Недопустимое значение частоты. Допустимые: {dict(self.RecurrenceFrequency.choices)}")

    def get_occurrences(self, start=None, end=None):
        """Возвращает все вхождения повторяющегося события в заданном диапазоне"""
        if not self.is_recurring:
            return [{
                'start': self.start_time,
                'end': self.end_time,
                'is_original': True
            }]

        start = start or self.start_time
        end = end or self.recurrence_end or (self.start_time + timezone.timedelta(days=365))

        rule = rrule.rrulestr(
            json.dumps(self.recurrence_rule),
            dtstart=self.start_time
        )

        occurrences = []
        for date in rule.between(start, end, inc=True):
            occurrences.append({
                'start': date,
                'end': date + (self.end_time - self.start_time),
                'is_original': date == self.start_time
            })

        return occurrences

    @classmethod
    def create_with_occurrences(cls, creator, **kwargs):
        """Создает событие с возможными повторениями"""
        event = cls(creator=creator, **kwargs)
        event.full_clean()
        event.save()
        
        # Для повторяющихся событий создаем UserEvent для каждого участника
        if event.event_type in [cls.EventType.GROUP, cls.EventType.DEADLINE]:
            event._create_participant_events()
        
        return event

    def _create_participant_events(self):
        """Создает UserEvent для всех участников группы (для групповых событий)"""
        from .services import GroupService
        
        if self.event_type == self.EventType.GROUP and self.group_id:
            group_members = GroupService.get_group_members(self.group_id)
            for member_id in group_members:
                UserEvent.objects.get_or_create(
                    user_id=member_id,
                    event=self,
                    defaults={'is_completed': False}
                )
        elif self.event_type == self.EventType.DEADLINE:
            # Для дедлайнов создаем записи только для студентов в группе
            group_members = GroupService.get_group_members(self.group_id, role='student')
            for member_id in group_members:
                UserEvent.objects.get_or_create(
                    user_id=member_id,
                    event=self,
                    defaults={'is_completed': False}
                )

class UserEvent(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_events',
        verbose_name="Пользователь"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='event_users',
        verbose_name="Событие"
    )
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено?")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Время выполнения")
    notes = models.TextField(blank=True, null=True, verbose_name="Заметки пользователя")

    class Meta:
        verbose_name = "Событие пользователя"
        verbose_name_plural = "События пользователей"
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем время выполнения при отметке как выполненное
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed and self.completed_at:
            self.completed_at = None
            
        super().save(*args, **kwargs)

    def get_event_details(self):
        """Возвращает детали события с учетом пользовательских данных"""
        return {
            'id': self.event.id,
            'title': self.event.title,
            'description': self.event.description,
            'start_time': self.event.start_time,
            'end_time': self.event.end_time,
            'event_type': self.event.event_type,
            'is_completed': self.is_completed,
            'notes': self.notes,
            'user_notes': self.notes
        }