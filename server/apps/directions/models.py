from django.db import models

class Department(models.Model):
    """Кафедры института"""
    name = models.CharField(max_length=255, verbose_name="Название кафедры")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Кафедра"
        verbose_name_plural = "Кафедры"

class EducationLevel(models.Model):
    """Уровни образования (бакалавриат, магистратура)"""
    name = models.CharField(max_length=100, verbose_name="Уровень образования")
    code = models.CharField(max_length=20, verbose_name="Код уровня")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Уровень образования"
        verbose_name_plural = "Уровни образования"

class Program(models.Model):
    """Образовательные программы"""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs', verbose_name="Кафедра")
    code = models.CharField(max_length=20, verbose_name="Код направления")
    name = models.CharField(max_length=255, verbose_name="Название направления")
    level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name='programs', verbose_name="Уровень")
    program_name = models.CharField(max_length=255, verbose_name="Название программы")
    form = models.CharField(max_length=50, default="Очная", verbose_name="Форма обучения")
    description = models.TextField(verbose_name="Описание программы")
    career_opportunities = models.TextField(verbose_name="Кем можно работать")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.program_name} ({self.level})"

    class Meta:
        verbose_name = "Программа"
        verbose_name_plural = "Программы"

class PartnerCompany(models.Model):
    """Компании-партнеры"""
    name = models.CharField(max_length=255, verbose_name="Название компании")
    logo = models.ImageField(upload_to='partners/', null=True, blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Партнер"
        verbose_name_plural = "Партнеры"

class ProgramFeature(models.Model):
    """Особенности программ"""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='features')
    title = models.CharField(max_length=255, verbose_name="Заголовок особенности")
    description = models.TextField(verbose_name="Описание")
    
    def __str__(self):
        return f"{self.program} - {self.title}"

    class Meta:
        verbose_name = "Особенность"
        verbose_name_plural = "Особенности"