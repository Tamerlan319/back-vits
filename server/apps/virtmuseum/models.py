from django.db import models
from server.settings.environments.storage_backends import YandexMediaStorage

class Audience(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название аудитории")
    description = models.TextField(blank=True, null=True, verbose_name="Описание аудитории")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Аудитория"
        verbose_name_plural = "Аудитории"

class Characteristic(models.Model):
    audience = models.ForeignKey('Audience', on_delete=models.CASCADE, related_name='characteristics', verbose_name="Аудитория")
    name = models.CharField(max_length=255, verbose_name="Название характеристики")
    value = models.CharField(max_length=255, verbose_name="Значение характеристики")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.name}: {self.value}"

    class Meta:
        verbose_name = "Характеристика"
        verbose_name_plural = "Характеристики"

class AudienceImage(models.Model):
    audience = models.ForeignKey(Audience, on_delete=models.CASCADE, related_name='images', verbose_name="Аудитория")
    image = models.ImageField(
        upload_to='audience_images/',
        storage=YandexMediaStorage(),  # или оставьте DEFAULT_FILE_STORAGE
        verbose_name="Изображение"
    )
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Описание изображения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Изображение для {self.audience.name}"

    class Meta:
        verbose_name = "Изображение аудитории"
        verbose_name_plural = "Изображения аудиторий"