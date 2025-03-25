from rest_framework import viewsets
from .models import Department, Program
from .serializers import DepartmentSerializer, ProgramSerializer

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Program.objects.select_related('department', 'level').prefetch_related('features')
    serializer_class = ProgramSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Фильтрация по уровню образования
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level__code=level)
        return queryset