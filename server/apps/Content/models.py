from django.db import models
from django.conf import settings
from server.settings.environments.storage_backends import YandexMediaStorage

class Banner(models.Model):
    image = models.ImageField(
        upload_to='banners/',
        storage=YandexMediaStorage()
    )
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'

    def __str__(self):
        return f"Баннер #{self.id}"

class Achievement(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(
        upload_to='achievements/',
        storage=YandexMediaStorage()
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Review(models.Model):
    author = models.CharField(max_length=150)
    course = models.CharField(max_length=150)
    text = models.TextField()
    image = models.ImageField(
        upload_to='reviews/',
        storage=YandexMediaStorage(),
        blank=True, 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.author} о курсе {self.course}"

class OrganizationDocument(models.Model):  
    title = models.CharField(max_length=255, verbose_name='Название документа')
    file = models.FileField(
        upload_to='organization_documents/',
        storage=YandexMediaStorage(),
        verbose_name='Файл документа'
    )

    class Meta:
        verbose_name = 'Документ организации'
        verbose_name_plural = 'Документы организации'

    def __str__(self):
        return f"{self.get_document_type_display()}: {self.title}"

class VideoContent(models.Model):    
    title = models.CharField(max_length=200, verbose_name='Название видео')
    video_url = models.URLField(verbose_name='Ссылка на видео (YouTube/Vimeo и т.д.)')
    description = models.TextField(blank=True, verbose_name='Описание видео')

    class Meta:
        verbose_name = 'Видео контент'
        verbose_name_plural = 'Видео контент'

    def __str__(self):
        return f"{self.title} ({self.get_page_display()})"