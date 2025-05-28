from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator, FileExtensionValidator

class Department(models.Model):
    """Кафедры института"""
    name = models.CharField(
        max_length=255,
        verbose_name="Название кафедры",
        validators=[
            MinLengthValidator(3, "Название должно содержать минимум 3 символа"),
            MaxLengthValidator(255, "Название слишком длинное")
        ]
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Кафедра"
        verbose_name_plural = "Кафедры"
        ordering = ['name']

class EducationLevel(models.Model):
    """Уровни образования (бакалавриат, магистратура)"""
    name = models.CharField(
        max_length=100,
        verbose_name="Уровень образования",
        validators=[MinLengthValidator(3)]
    )
    code = models.CharField(
        max_length=20,
        verbose_name="Код уровня",
        unique=True,
        validators=[MinLengthValidator(2)]
    )

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Уровень образования"
        verbose_name_plural = "Уровни образования"
        ordering = ['name']

class Program(models.Model):
    """Образовательные программы"""
    FORMS = [
        ('FT', 'Очная'),
        ('PT', 'Очно-заочная'),
        ('DL', 'Заочная'),
    ]

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name="Кафедра"
    )
    code = models.CharField(
        max_length=20,
        verbose_name="Код направления",
        validators=[MinLengthValidator(2)]
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Название направления",
        validators=[MinLengthValidator(5)]
    )
    level = models.ForeignKey(
        EducationLevel,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name="Уровень"
    )
    program_name = models.CharField(
        max_length=255,
        verbose_name="Название программы",
        validators=[MinLengthValidator(5)]
    )
    form = models.CharField(
        max_length=50,
        choices=FORMS,
        default='FT',
        verbose_name="Форма обучения"
    )
    description = models.TextField(
        verbose_name="Описание программы",
        validators=[MinLengthValidator(50)]
    )
    career_opportunities = models.TextField(
        verbose_name="Кем можно работать",
        validators=[MinLengthValidator(20)]
    )
    updated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(null=True, default=True, verbose_name="Активна")

    def __str__(self):
        return f"{self.code} {self.program_name} ({self.get_form_display()})"

    class Meta:
        verbose_name = "Программа"
        verbose_name_plural = "Программы"
        ordering = ['code', 'program_name']
        unique_together = ('code', 'program_name', 'form')

class PartnerCompany(models.Model):
    """Компании-партнеры"""
    name = models.CharField(
        max_length=255,
        verbose_name="Название компании",
        unique=True,
        validators=[MinLengthValidator(3)]
    )
    logo = models.ImageField(
        upload_to='partners/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ]
    )
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Партнер"
        verbose_name_plural = "Партнеры"
        ordering = ['name']

class ProgramFeature(models.Model):
    """Особенности программ"""
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='features'
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок особенности",
        validators=[MinLengthValidator(5)]
    )
    description = models.TextField(
        verbose_name="Описание",
        validators=[MinLengthValidator(10)]
    )
    order = models.PositiveIntegerField(null=True, default=0, verbose_name="Порядок")

    def __str__(self):
        return f"{self.program}: {self.title}"

    class Meta:
        verbose_name = "Особенность"
        verbose_name_plural = "Особенности"
        ordering = ['order', 'title']