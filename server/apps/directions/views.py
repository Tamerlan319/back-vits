from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from .models import Department, EducationLevel, Program, PartnerCompany, ProgramFeature
from .serializers import (
    DepartmentSerializer, EducationLevelSerializer,
    ProgramSerializer, ProgramListSerializer,
    PartnerCompanySerializer, ProgramFeatureSerializer
)
from .filters import ProgramFilter

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('name')
    serializer_class = DepartmentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    
    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response(
                {'error': 'Кафедра не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

class EducationLevelViewSet(viewsets.ModelViewSet):
    queryset = EducationLevel.objects.all().order_by('name')
    serializer_class = EducationLevelSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    
    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response(
                {'error': 'Уровень образования не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.select_related(
        'department', 'level'
    ).prefetch_related(
        'features'
    ).order_by('code', 'program_name')
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProgramFilter
    search_fields = ['code', 'name', 'program_name']
    ordering_fields = ['code', 'program_name', 'created_at']
    ordering = ['code']
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProgramListSerializer
        return ProgramSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset().filter(is_active=True))
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            raise ValidationError(str(e))
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        program = self.get_object()
        program.is_active = not program.is_active
        program.save()
        return Response(
            {'status': 'success', 'is_active': program.is_active},
            status=status.HTTP_200_OK
        )
    
    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response(
                {'error': 'Программа не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

class PartnerCompanyViewSet(viewsets.ModelViewSet):
    queryset = PartnerCompany.objects.all().order_by('name')
    serializer_class = PartnerCompanySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    
    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response(
                {'error': 'Компания-партнер не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

class ProgramFeatureViewSet(viewsets.ModelViewSet):
    queryset = ProgramFeature.objects.all().order_by('order', 'title')
    serializer_class = ProgramFeatureSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['program']
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    
    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response(
                {'error': 'Особенность программы не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)