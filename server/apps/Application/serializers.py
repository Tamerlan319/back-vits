from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from .models import Application, ApplicationAttachment, ApplicationStatusLog, ApplicationType
from server.apps.users.serializers import UserSerializer
import os
import re

class ApplicationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationType
        fields = ['id', 'name', 'code']
    
    def validate_code(self, value):
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
        if obj.file and hasattr(obj.file, 'url'):
            return obj.file.url
        return None

class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ApplicationStatusLog
        fields = '__all__'
        read_only_fields = ['changed_at']

class ApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type = ApplicationTypeSerializer(read_only=True)
    type_display = serializers.SerializerMethodField()
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
    
    def get_type_display(self, obj):
        return obj.type.name if obj.type else None

class ApplicationCreateSerializer(serializers.ModelSerializer):
    type = serializers.PrimaryKeyRelatedField(queryset=ApplicationType.objects.all())
    attachments = serializers.ListField(
        child=serializers.FileField(max_length=100000, use_url=False),
        required=False,
        write_only=True
    )

    class Meta:
        model = Application
        fields = ['type', 'description', 'attachments']
    
    def validate(self, data):
        user = self.context['request'].user
        if Application.objects.filter(user=user, status='pending').count() >= 5:
            raise serializers.ValidationError("Максимум 5 заявлений в обработке одновременно")
        return data
    
    def create(self, validated_data):
        attachments = validated_data.pop('attachments', [])
        application = Application.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        for file in attachments:
            ApplicationAttachment.objects.create(application=application, file=file)
        return application

class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status', 'admin_comment']
    
    def validate_status(self, value):
        if value not in dict(Application.STATUS_CHOICES):
            raise serializers.ValidationError("Неверный статус")
        return value