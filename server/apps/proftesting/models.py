from django.db import models
from django.contrib.auth import get_user_model
from server.apps.directions.models import Program, EducationLevel

User = get_user_model()

class QuestionGroup(models.Model):
    """Группы вопросов (может быть привязана к уровню образования)"""
    name = models.CharField(max_length=100)
    education_level = models.ForeignKey(
        EducationLevel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    def __str__(self):
        return self.name

class Question(models.Model):
    """Вопросы теста"""
    text = models.TextField(verbose_name="Текст вопроса")
    group = models.ForeignKey(
        QuestionGroup, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='questions'
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.text[:50]}..." if len(self.text) > 50 else self.text

class AnswerOption(models.Model):
    """Варианты ответов на вопросы"""
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='options'
    )
    text = models.CharField(max_length=255)
    # Связь с программами и вес ответа для каждой
    program_weights = models.ManyToManyField(
        Program,
        through='AnswerProgramWeight',
        related_name='answer_options'
    )
    # updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.question.text[:30]} - {self.text[:20]}"

class AnswerProgramWeight(models.Model):
    """Промежуточная модель для весов ответов по программам"""
    answer_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    weight = models.IntegerField(default=1)
    
    class Meta:
        unique_together = ('answer_option', 'program')

class TestSession(models.Model):
    """Сессия тестирования пользователя"""
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    education_level = models.ForeignKey(
        EducationLevel, 
        on_delete=models.SET_NULL, 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Тест {self.id} ({self.education_level})"

class UserAnswer(models.Model):
    """Ответы пользователя"""
    session = models.ForeignKey(
        TestSession, 
        on_delete=models.CASCADE, 
        related_name='answers'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(AnswerOption, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('session', 'question')

class TestResult(models.Model):
    """Результаты тестирования"""
    session = models.OneToOneField(
        TestSession, 
        on_delete=models.CASCADE, 
        related_name='result'
    )
    recommended_programs = models.ManyToManyField(Program)
    created_at = models.DateTimeField(auto_now_add=True)
    # updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Результат теста {self.session.id}"