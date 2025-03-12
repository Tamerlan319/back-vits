from rest_framework import serializers
from .models import Audience, Characteristic, AudienceImage

class AudienceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudienceImage
        fields = ['image', 'description']

class CharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Characteristic
        fields = ['name', 'value']

class CharacteristicCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Characteristic
        fields = ['name', 'value']

class AudienceSerializer(serializers.ModelSerializer):
    images = AudienceImageSerializer(many=True, read_only=True)
    characteristics = CharacteristicSerializer(many=True, read_only=True)

    class Meta:
        model = Audience
        fields = ['id', 'name', 'description', 'images', 'characteristics']