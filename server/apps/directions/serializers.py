from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.validators import validate_image_file_extension
from .models import Department, EducationLevel, Program, PartnerCompany, ProgramFeature, FacultyMember

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']
        extra_kwargs = {
            'name': {
                'min_length': 3,
                'max_length': 255
            }
        }

class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = ['id', 'name', 'code']
        extra_kwargs = {
            'name': {'min_length': 3},
            'code': {'min_length': 2}
        }

class PartnerCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCompany
        fields = ['id', 'name', 'logo', 'website']
        extra_kwargs = {
            'name': {
                'min_length': 3,
                'max_length': 255
            },
            'logo': {
                'validators': [validate_image_file_extension]
            }
        }

class ProgramFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramFeature
        fields = ['id', 'title', 'description', 'order']
        extra_kwargs = {
            'title': {'min_length': 5},
            'description': {'min_length': 10}
        }

class ProgramSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True
    )
    level = EducationLevelSerializer(read_only=True)
    level_id = serializers.PrimaryKeyRelatedField(
        queryset=EducationLevel.objects.all(),
        source='level',
        write_only=True
    )
    features = ProgramFeatureSerializer(many=True, read_only=True)
    form_display = serializers.CharField(source='get_form_display', read_only=True)
    career_opportunities_list = serializers.SerializerMethodField()

    class Meta:
        model = Program
        fields = [
            'id', 'code', 'name', 'program_name', 'department', 'department_id',
            'level', 'level_id', 'form', 'form_display', 'description',
            'career_opportunities', 'career_opportunities_list', 'features',
            'is_active', 'updated_at'
        ]
        extra_kwargs = {
            'code': {'min_length': 2},
            'name': {'min_length': 5},
            'program_name': {'min_length': 5},
            'description': {'min_length': 50},
            'career_opportunities': {'min_length': 20}
        }

    def get_career_opportunities_list(self, obj):
        return [x.strip() for x in obj.career_opportunities.split('\n') if x.strip()]

    def validate_code(self, value):
        if not value.isalnum():
            raise ValidationError("Код программы должен содержать только буквы и цифры")
        return value

    def validate(self, data):
        if 'department' in data and 'level' in data:
            department = data['department']
            level = data['level']

            if not department.programs.filter(level=level).exists():
                raise ValidationError(
                    "Выбранная кафедра не предлагает программы на этом уровне образования"
                )
        return data

class ProgramListSerializer(serializers.ModelSerializer):
    department = serializers.StringRelatedField()
    level = serializers.StringRelatedField()
    form_display = serializers.CharField(source='get_form_display')

    class Meta:
        model = Program
        fields = [
            'id', 'code', 'program_name', 'department', 'level',
            'form_display', 'is_active'
        ]

class DepartmentWithProgramsSerializer(serializers.ModelSerializer):
    programs = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'programs']
    
    def get_programs(self, obj):
        # Получаем все программы кафедры с полными связанными данными
        programs = obj.programs.select_related(
            'level'
        ).prefetch_related(
            'features'
        ).filter(is_active=True)
        
        return ProgramSerializer(programs, many=True, context=self.context).data

class DepartmentShortSerializer(serializers.ModelSerializer):
    """Сокращенный сериализатор для кафедры"""
    class Meta:
        model = Department
        fields = ['id', 'name']
        read_only_fields = ['id', 'name']

class FacultyMemberSerializer(serializers.ModelSerializer):
    department = DepartmentShortSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=True
    )
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FacultyMember
        fields = [
            'id',
            'department', 'department_id',
            'name', 'position', 'degree',
            'email', 'phone', 'photo', 'photo_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'photo_url']
        extra_kwargs = {
            'photo': {'write_only': True}
        }

    def get_photo_url(self, obj):
        if obj.photo:
            return self.context['request'].build_absolute_uri(obj.photo.url)
        return None

    def validate_position(self, value):
        """Проверка должности"""
        if len(value) < 3:
            raise serializers.ValidationError("Должность должна содержать минимум 3 символа")
        return value

    def validate_phone(self, value):
        """Проверка телефона"""
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Телефон должен начинаться с '+'")
        return value