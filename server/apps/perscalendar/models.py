from django.db import models
from django.core.exceptions import ValidationError
from server.apps.users.models import User, Group

class Event(models.Model):
    class EventType(models.TextChoices):
        PERSONAL = 'personal', 'Личное'
        GROUP = 'group', 'Групповое'
        GLOBAL = 'global', 'Общее'
        DEADLINE = 'deadline', 'Дедлайн'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event_type = models.CharField(max_length=10, choices=EventType.choices, default=EventType.PERSONAL)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_events'
    )
    group_id = models.PositiveIntegerField(null=True, blank=True)  # Внешний ID группы из сервиса групп
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['start_time']

    def clean(self):
        if self.event_type == 'group' and not self.group_id:
            raise ValidationError("Групповые события должны быть привязаны к группе.")
        if self.start_time >= self.end_time:
            raise ValidationError("Время окончания должно быть позже времени начала.")

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
    notes = models.TextField(blank=True, null=True, verbose_name="Заметки пользователя")

    class Meta:
        verbose_name = "Событие пользователя"
        verbose_name_plural = "События пользователей"
        unique_together = ('user', 'event')  # Чтобы не было дубликатов

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"