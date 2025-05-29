from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Application, ApplicationAttachment, ApplicationStatusLog
from .serializers import (
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusUpdateSerializer,
    ApplicationAttachmentSerializer
)
from server.apps.users.models import User
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError

@api_view(['GET'])
def get_application_types(request):
    types = Application.TYPE_CHOICES
    data = [{'value': value, 'label': label} for value, label in types]
    return Response(data)

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'type', 'user__role']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        elif self.action == 'update_status':
            return ApplicationStatusUpdateSerializer
        return ApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return super().get_queryset()
        return super().get_queryset().filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        if self.request.user.role != 'admin':
            raise PermissionDenied("Только администраторы могут изменять статус заявлений")
        
        application = self.get_object()
        serializer = self.get_serializer(application, data=request.data, partial=True)
        
        if serializer.is_valid():
            old_status = application.status
            new_status = serializer.validated_data.get('status', old_status)
            comment = serializer.validated_data.get('admin_comment', '')
            
            if old_status != new_status:
                ApplicationStatusLog.objects.create(
                    application=application,
                    changed_by=request.user,
                    from_status=old_status,
                    to_status=new_status,
                    comment=comment
                )
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        query = request.query_params.get('q', '')
        queryset = self.filter_queryset(self.get_queryset())
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query)
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ApplicationAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ApplicationAttachment.objects.all()
    serializer_class = ApplicationAttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return super().get_queryset()
        return super().get_queryset().filter(application__user=user)
    
    def perform_create(self, serializer):
        application_id = self.request.data.get('application')
        try:
            application = Application.objects.get(id=application_id)
            
            # Проверка прав доступа
            if application.user != self.request.user and self.request.user.role != 'admin':
                raise PermissionDenied("Вы не можете добавлять файлы к этому заявлению")
            
            # Проверка статуса заявления
            if application.status != 'pending':
                raise ValidationError(
                    "Файлы можно добавлять только к заявлениям со статусом 'На рассмотрении'"
                )
            
            # Проверка количества вложений
            attachments_count = application.attachments.count()
            if attachments_count >= 5:
                raise ValidationError(
                    "Максимальное количество вложений - 5. Удалите некоторые файлы перед добавлением новых."
                )
            
            serializer.save(application=application)
            
        except Application.DoesNotExist:
            raise ValidationError("Заявление не найдено")