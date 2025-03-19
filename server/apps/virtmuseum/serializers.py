from rest_framework import serializers
from .models import Audience, Characteristic, AudienceImage

class AudienceImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudienceImage
        fields = ['audience', 'image', 'description']

class CharacteristicCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Characteristic
        fields = ['audience', 'name', 'value']

class AudienceCreateUpdateSerializer(serializers.ModelSerializer):
    images = AudienceImageCreateSerializer(many=True, required=False)
    characteristics = CharacteristicCreateSerializer(many=True, required=False)

    class Meta:
        model = Audience
        fields = ['id', 'name', 'description', 'images', 'characteristics']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        characteristics_data = validated_data.pop('characteristics', [])
        
        # Создаем аудиторию
        audience = Audience.objects.create(**validated_data)
        
        # Создаем связанные изображения
        for image_data in images_data:
            AudienceImage.objects.create(audience=audience, **image_data)
        
        # Создаем связанные характеристики
        for characteristic_data in characteristics_data:
            Characteristic.objects.create(audience=audience, **characteristic_data)
        
        return audience

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])
        characteristics_data = validated_data.pop('characteristics', [])
        
        # Обновляем основные данные аудитории
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        
        # Удаляем старые изображения и создаем новые
        instance.images.all().delete()
        for image_data in images_data:
            AudienceImage.objects.create(audience=instance, **image_data)
        
        # Удаляем старые характеристики и создаем новые
        instance.characteristics.all().delete()
        for characteristic_data in characteristics_data:
            Characteristic.objects.create(audience=instance, **characteristic_data)
        
        return instance