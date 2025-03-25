from rest_framework import serializers
from .models import Department, EducationLevel, Program, PartnerCompany, ProgramFeature

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = '__all__'

class PartnerCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCompany
        fields = '__all__'

class ProgramFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramFeature
        fields = '__all__'

class ProgramSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer()
    level = EducationLevelSerializer()
    features = ProgramFeatureSerializer(many=True)
    career_opportunities = serializers.SerializerMethodField()
    
    class Meta:
        model = Program
        fields = '__all__'
    
    def get_career_opportunities(self, obj):
        return [x.strip() for x in obj.career_opportunities.split('\n') if x.strip()]