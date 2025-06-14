from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from .models import Application, ApplicationAttachment, ApplicationStatusLog, ApplicationType
from server.apps.users.serializers import UserSerializer
import os

class ApplicationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationType
        fields = ['id', 'name', 'code', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_code(self, value):
        """Проверка, что код содержит только допустимые символы"""
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError(
                "Код может содержать только строчные латинские буквы, цифры и подчеркивания"
            )
        return value

class ApplicationAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ApplicationAttachment
        fields = ['id', 'file', 'file_url', 'uploaded_at']
        read_only_fields = ['uploaded_at']
        extra_kwargs = {
            'file': {
                'validators': [
                    FileExtensionValidator(allowed_extensions=['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.zip'])
                ]
            }
        }
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        
        # Генерируем подписанный URL (доступен только авторизованным пользователям)
        if obj.file and hasattr(obj.file, 'url'):
            url = obj.file.storage.url(
                obj.file.name,
            )
            return url
        return None
    
    def validate_file(self, value):
        # Проверка размера файла (5 MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Максимальный размер файла 5MB. Ваш файл {round(value.size/1024/1024, 2)}MB"
            )
        
        # Проверка расширения файла
        ext = os.path.splitext(value.name)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.zip']
        if ext not in valid_extensions:
            raise serializers.ValidationError(
                f"Неподдерживаемый тип файла. Разрешенные типы: {', '.join(valid_extensions)}"
            )
        
        return value

class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ApplicationStatusLog
        fields = '__all__'
        read_only_fields = ['changed_at']

class ApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type = ApplicationTypeSerializer(read_only=True)  # Изменяем на сериализатор типа
    attachments = ApplicationAttachmentSerializer(many=True, read_only=True)
    status_logs = ApplicationStatusLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'user', 'type', 'type_display', 'description', 
            'status', 'status_display', 'created_at', 'updated_at', 
            'admin_comment', 'attachments', 'status_logs'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'status_logs']

class ApplicationCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(
        child=serializers.FileField(
            max_length=100000,
            allow_empty_file=True,
            use_url=False,
            validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'zip', 'rar'])]
        ),
        required=False,
        write_only=True
    )

    class Meta:
        model = Application
        fields = ['type', 'description', 'attachments']
    
    def validate(self, data):
        user = self.context['request'].user
        pending_count = Application.objects.filter(
            user=user, 
            status='pending'
        ).count()
        if pending_count >= 5:
            raise serializers.ValidationError(
                "У вас слишком много заявлений в обработке. Максимум 5 одновременно."
            )
        
        # Проверка количества файлов
        if 'attachments' in data and len(data['attachments']) > 5:
            raise serializers.ValidationError(
                "Максимальное количество вложений - 5."
            )
            
        return data
    
    def create(self, validated_data):
        attachments = validated_data.pop('attachments', [])
        application = Application.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        
        # Создаем прикрепленные файлы
        for file in attachments:
            ApplicationAttachment.objects.create(
                application=application,
                file=file
            )
            
        return application

class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status', 'admin_comment']
    
    def validate_status(self, value):
        valid_statuses = dict(Application.STATUS_CHOICES).keys()
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Неверный статус. Допустимые значения: {', '.join(valid_statuses)}"
            )
        return value