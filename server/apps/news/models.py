from django.db import models
from django.conf import settings
from server.settings.environments.storage_backends import YandexMediaStorage

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    description = models.TextField(blank=True, null=True, verbose_name="Описание категории")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

class News(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок новости")
    content = models.TextField(verbose_name="Содержание новости")
    image = models.ImageField(
        upload_to='news_images/',
        storage=YandexMediaStorage(),
        blank=True,
        null=True,
        verbose_name="Изображение"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_published = models.BooleanField(default=False, verbose_name="Опубликовано")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='news', verbose_name="Автор")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='news', verbose_name="Категория")
    tags = models.ManyToManyField(Tag, related_name='news', blank=True, verbose_name="Теги")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Проверка количества изображений перед сохранением
        if self.pk and self.images.count() > 6:
            raise ValidationError("Нельзя прикрепить более 6 изображений к новости")
        super().save(*args, **kwargs)

class NewsImage(models.Model):
    news = models.ForeignKey(News, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='news_images/',
        storage=YandexMediaStorage()  # или оставьте DEFAULT_FILE_STORAGE
    )

    def __str__(self):
        return f"Image for {self.news.title}"

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"

class Comment(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='comments', verbose_name="Новость")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', verbose_name="Автор")
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Комментарий от {self.author} к новости {self.news.title}"

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['-created_at']

class Like(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='likes', verbose_name="Новость")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes', verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Лайк от {self.user} для новости {self.news.title}"

    class Meta:
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"
        unique_together = ('news', 'user')  # Один пользователь может лайкнуть новость только один раз