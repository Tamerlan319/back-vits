from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from server.apps.directions.models import EducationLevel, Program
from .models import (
    QuestionGroup,
    Question,
    TestSession,
    UserAnswer,
    TestResult,
    AnswerOption
)
from .serializers import (
    QuestionGroupSerializer,
    QuestionSerializer,
    TestSessionSerializer,
    UserAnswerSerializer,
    TestResultSerializer
)

class EducationLevelsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        levels = EducationLevel.objects.all().values('id', 'name', 'code')
        return Response(levels)

class QuestionGroupsView(generics.ListAPIView):
    serializer_class = QuestionGroupSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        level_id = self.request.query_params.get('level_id')
        if level_id:
            return QuestionGroup.objects.filter(
                Q(education_level_id=level_id) | Q(education_level__isnull=True))
        return QuestionGroup.objects.all()

class QuestionsView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        group_id = self.request.query_params.get('group_id')
        if group_id:
            return Question.objects.filter(group_id=group_id)
        return Question.objects.none()

class StartTestView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        level_id = request.data.get('level_id')
        if not level_id:
            return Response(
                {'error': 'level_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = TestSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            education_level_id=level_id
        )
        
        serializer = TestSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SubmitAnswerView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, session_id):
        try:
            session = TestSession.objects.get(id=session_id)
        except TestSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Валидация входных данных
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of answers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        answers_to_create = []
        errors = []
        
        for answer_data in request.data:
            try:
                question_id = int(answer_data.get('question'))
                answer_id = int(answer_data.get('answer'))
                
                # Проверяем существование вопроса и ответа
                Question.objects.get(id=question_id)
                AnswerOption.objects.get(id=answer_id)
                
                answers_to_create.append(
                    UserAnswer(
                        session=session,
                        question_id=question_id,
                        answer_id=answer_id
                    )
                )
            except (ValueError, TypeError):
                errors.append({
                    'error': 'Invalid ID format',
                    'data': answer_data
                })
            except (Question.DoesNotExist, AnswerOption.DoesNotExist):
                errors.append({
                    'error': 'Question or Answer not found',
                    'data': answer_data
                })
        
        if errors:
            return Response(
                {'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Удаляем старые ответы на эти вопросы
        question_ids = [a.question_id for a in answers_to_create]
        UserAnswer.objects.filter(
            session=session,
            question_id__in=question_ids
        ).delete()
        
        # Создаем новые ответы
        UserAnswer.objects.bulk_create(answers_to_create)
        
        return Response({
            'status': 'success',
            'saved_answers': len(answers_to_create)
        })

class CompleteTestView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, session_id):
        try:
            session = TestSession.objects.get(id=session_id)
        except TestSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Подсчет результатов
        from django.db.models import Sum
        from .models import AnswerProgramWeight
        
        # Получаем все ответы пользователя
        user_answers = UserAnswer.objects.filter(session=session)
        answer_ids = [answer.answer_id for answer in user_answers]
        
        # Считаем суммарные веса по программам
        program_scores = (
            AnswerProgramWeight.objects
            .filter(answer_option_id__in=answer_ids)
            .values('program')
            .annotate(total_score=Sum('weight'))
            .order_by('-total_score')
        )
        
        # Берем топ-5 программ
        top_program_ids = [item['program'] for item in program_scores[:5]]
        top_programs = Program.objects.filter(id__in=top_program_ids)
        
        # Создаем результат
        result = TestResult.objects.create(session=session)
        result.recommended_programs.set(top_programs)
        
        # Помечаем сессию как завершенную
        session.completed = True
        session.save()
        
        serializer = TestResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TestResultView(generics.RetrieveAPIView):
    serializer_class = TestResultSerializer
    permission_classes = [AllowAny]
    queryset = TestResult.objects.all()
    lookup_field = 'session_id'
    lookup_url_kwarg = 'session_id'