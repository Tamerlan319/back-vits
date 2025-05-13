from rest_framework import serializers
from .models import (
    QuestionGroup,
    Question,
    AnswerOption,
    TestSession,
    UserAnswer,
    TestResult
)
from server.apps.directions.serializers import ProgramSerializer

class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['id', 'text']

class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'options', 'order']

class QuestionGroupSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuestionGroup
        fields = ['id', 'name', 'questions']

class TestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSession
        fields = ['id', 'education_level', 'created_at', 'completed']

class UserAnswerSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all()
    )
    answer = serializers.PrimaryKeyRelatedField(
        queryset=AnswerOption.objects.all()
    )
    
    class Meta:
        model = UserAnswer
        fields = ['question', 'answer']

class TestResultSerializer(serializers.ModelSerializer):
    recommended_programs = ProgramSerializer(many=True, read_only=True)
    
    class Meta:
        model = TestResult
        fields = ['id', 'recommended_programs', 'created_at']