from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Application, ApplicationAttachment, ApplicationStatusLog, ApplicationType
from .serializers import (
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusUpdateSerializer,
    ApplicationAttachmentSerializer,
    ApplicationTypeSerializer
)
from server.apps.users.models import User
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
import os

@api_view(['GET'])
def get_application_types(request):
    types = Application.TYPE_CHOICES
    data = [{'value': value, 'label': label} for value, label in types]
    return Response(data)

class ApplicationTypeViewSet(viewsets.ModelViewSet):
    queryset = ApplicationType.objects.all().order_by('name')
    serializer_class = ApplicationTypeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'  # Для удобства используем code вместо id
    
    def get_permissions(self):
        """Только администраторы могут изменять типы"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, code=None):
        """Переключение активности типа"""
        if not request.user.is_admin:
            raise PermissionDenied("Только администраторы могут изменять активность типов")
        
        app_type = self.get_object()
        app_type.is_active = not app_type.is_active
        app_type.save()
        
        return Response({
            'status': 'success',
            'is_active': app_type.is_active,
            'message': f"Тип '{app_type.name}' теперь {'активен' if app_type.is_active else 'неактивен'}"
        })

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
        # Просто вызываем save(), user будет установлен в сериализаторе
        serializer.save()
    
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class ApplicationAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ApplicationAttachment.objects.all()
    serializer_class = ApplicationAttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return super().get_queryset()
        return super().get_queryset().filter(application__user=user)
    
    def validate_file(self, file):
        """Валидация файла перед сохранением"""
        # 1. Проверка размера файла (5MB максимум)
        max_size = 5 * 1024 * 1024
        if file.size > max_size:
            raise ValidationError(
                f"Максимальный размер файла 5MB. Ваш файл {round(file.size/1024/1024, 2)}MB"
            )
        
        # 2. Проверка расширения
        valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.zip']
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError(
                f"Неподдерживаемый тип файла. Разрешенные: {', '.join(valid_extensions)}"
            )
        
        # 3. Проверка имени файла (опционально)
        if len(file.name) > 100:
            raise ValidationError("Слишком длинное имя файла (макс. 100 символов)")

    def perform_create(self, serializer):
        application_id = self.request.data.get('application')
        file = self.request.FILES.get('file')
        
        try:
            application = Application.objects.get(id=application_id)
            
            # 1. Проверка прав доступа
            if application.user != self.request.user and self.request.user.role != 'admin':
                raise PermissionDenied("Вы не можете добавлять файлы к этому заявлению")
            
            # 2. Проверка статуса заявления
            if application.status != 'pending':
                raise ValidationError(
                    "Файлы можно добавлять только к заявлениям со статусом 'На рассмотрении'"
                )
            
            # 3. Проверка количества вложений
            if application.attachments.count() >= 5:
                raise ValidationError(
                    "Максимальное количество вложений - 5. Удалите некоторые файлы перед добавлением новых."
                )
            
            # 4. Валидация файла
            if file:
                self.validate_file(file)
            else:
                raise ValidationError("Файл не был загружен")
            
            # Сохранение
            serializer.save(
                application=application,
                file=file
            )
            
        except ObjectDoesNotExist:
            raise ValidationError("Заявление не найдено")
        except Exception as e:
            raise ValidationError(str(e))

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except (PermissionDenied, ValidationError) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )