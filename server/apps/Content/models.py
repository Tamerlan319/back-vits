from django.db import models
from django.conf import settings

class Banner(models.Model):
    image = models.ImageField(upload_to='banners/')
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)  # Добавлено поле для сортировки

    class Meta:
        ordering = ['order']
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'

    def __str__(self):
        return f"Баннер #{self.id}"

class Achievement(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='achievements/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Review(models.Model):
    author = models.CharField(max_length=150)  # Просто текстовое поле
    course = models.CharField(max_length=150)
    text = models.TextField()
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.author} о курсе {self.course}"