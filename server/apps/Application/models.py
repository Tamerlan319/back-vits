from django.db import models
from django.contrib.auth import get_user_model
from server.settings.environments.storage_backends import PrivateMediaStorage
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from server.settings.environments.base import DEBUG_SOCKETS

User = get_user_model()

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    
    TYPE_CHOICES = [
        ('academic', 'Академический отпуск'),
        ('translation', 'Перевод на другой факультет'),
        ('reference', 'Справка об обучении'),
        ('retake', 'Пересдача экзамента'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="Тип заявления")
    description = models.TextField(verbose_name="Текст заявления")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    admin_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий администратора")
    
    class Meta:
        verbose_name = "Заявление"
        verbose_name_plural = "Заявления"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заявление от #{self.user.username}"

class ApplicationAttachment(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(
        upload_to='applications/attachments/',
        storage=PrivateMediaStorage(),  # Используем приватное хранилище
        verbose_name="Файл"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    
    class Meta:
        verbose_name = "Приложение к заявлению"
        verbose_name_plural = "Приложения к заявлениям"
    
    def __str__(self):
        return f"Приложение к заявлению #{self.application.id}"

class ApplicationStatusLog(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='status_logs')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    from_status = models.CharField(max_length=50)
    to_status = models.CharField(max_length=50)
    comment = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Лог изменения статуса"
        verbose_name_plural = "Логи изменений статусов"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"Изменение статуса заявления #{self.application.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if DEBUG_SOCKETS:
            self.send_notification()

    def send_notification(self):
        channel_layer = get_channel_layer()
        status_display = dict(Application.STATUS_CHOICES).get(self.to_status, self.to_status)
        
        message = f"Статус вашего заявления изменен: {status_display}"
        if self.comment:
            message += f". Комментарий: {self.comment}"
        
        async_to_sync(channel_layer.group_send)(
            f'user_{self.application.user.id}',
            {
                'type': 'notify_user',
                'message': message,
                'application_id': self.application.id,
                'status': self.to_status
            }
        )