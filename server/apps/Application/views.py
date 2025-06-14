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
from rest_framework.permissions import IsAuthenticated, IsAdminUser

@api_view(['GET'])
def get_application_types(request):
    """Возвращает активные типы заявлений для выпадающих списков"""
    types = ApplicationType.objects.filter(is_active=True).order_by('name')
    data = [{'value': type.code, 'label': type.name} for type in types]
    return Response(data)

class ApplicationTypeViewSet(viewsets.ModelViewSet):
    queryset = ApplicationType.objects.all().order_by('name')
    serializer_class = ApplicationTypeSerializer
    lookup_field = 'code'
    
    def get_permissions(self):
        if self.request.method == 'POST' and self.action == 'create':
            return [IsAdminUser()]
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @api_view(['GET', 'POST'])
    def application_types(request):
        if request.method == 'GET':
            types = ApplicationType.objects.all().order_by('name')
            data = [{'value': type.id, 'label': type.name} for type in types]
            return Response(data)
        
        elif request.method == 'POST':
            if not request.user.is_authenticated or request.user.role != 'admin':
                return Response(
                    {"error": True, "message": "Только администраторы могут создавать типы"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = ApplicationTypeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        if self.request.user.role != 'admin':
            return Response(
                {"detail": "Только администраторы могут изменять статус"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        serializer = self.get_serializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

@api_view(['GET'])
def get_application_types(request):
    types = ApplicationType.objects.all().order_by('name')
    data = [{'value': type.id, 'label': type.name} for type in types]
    return Response(data)

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