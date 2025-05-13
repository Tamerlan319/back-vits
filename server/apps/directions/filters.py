import django_filters
from .models import Program

class ProgramFilter(django_filters.FilterSet):
    department = django_filters.CharFilter(field_name='department__name', lookup_expr='icontains')
    level = django_filters.CharFilter(field_name='level__code')
    is_active = django_filters.BooleanFilter()
    form = django_filters.ChoiceFilter(choices=Program.FORMS)
    
    class Meta:
        model = Program
        fields = ['department', 'level', 'form', 'is_active']