import django_filters
from .models import Application
from django.db.models import Q

class ApplicationFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Application
        fields = ['status', 'type', 'user__role']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value)
        )