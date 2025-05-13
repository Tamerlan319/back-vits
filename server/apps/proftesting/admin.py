from django.contrib import admin
from .models import (
    QuestionGroup,
    Question,
    AnswerOption,
    AnswerProgramWeight,
    TestSession,
    UserAnswer,
    TestResult
)

class AnswerProgramWeightInline(admin.TabularInline):
    model = AnswerProgramWeight
    extra = 1

class AnswerOptionAdmin(admin.ModelAdmin):
    inlines = [AnswerProgramWeightInline]
    list_display = ('question', 'text')
    list_filter = ('question__group',)

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'group', 'order')
    list_filter = ('group',)
    ordering = ('order',)

class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0

class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'education_level', 'created_at', 'completed')
    list_filter = ('education_level', 'completed')
    inlines = [UserAnswerInline]

class TestResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'created_at')
    filter_horizontal = ('recommended_programs',)

admin.site.register(QuestionGroup)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AnswerOption, AnswerOptionAdmin)
admin.site.register(TestSession, TestSessionAdmin)
admin.site.register(TestResult, TestResultAdmin)