from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action   
from .models import Audience, Characteristic, AudienceImage
from .serializers import AudienceCreateUpdateSerializer, CharacteristicCreateSerializer, AudienceImageCreateSerializer
from .mixins import CacheListRetrieveMixin
from django.conf import settings

class AudienceImageViewSet(CacheListRetrieveMixin, viewsets.ModelViewSet):
    queryset = AudienceImage.objects.all()
    serializer_class = AudienceImageCreateSerializer

class CharacteristicViewSet(CacheListRetrieveMixin, viewsets.ModelViewSet):
    queryset = Characteristic.objects.all()
    serializer_class = CharacteristicCreateSerializer

class AudienceViewSet(CacheListRetrieveMixin, viewsets.ModelViewSet):
    queryset = Audience.objects.all()
    serializer_class = AudienceCreateUpdateSerializer

    def get_cache_keys(self, instance):
        """Генерирует ключи кеша для инвалидации"""
        return [
            f"api_audience_{instance.pk}",  # Кеш конкретного объекта
            "api_audiences_list",           # Кеш списка объектов
        ]

    def perform_create(self, serializer):
        instance = serializer.save()
        if settings.CACHE_ENABLED:
            cache.delete("api_audiences_list")
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        if settings.CACHE_ENABLED:
            for key in self.get_cache_keys(instance):
                cache.delete(key)
        return instance

    def perform_destroy(self, instance):
        if settings.CACHE_ENABLED:
            for key in self.get_cache_keys(instance):
                cache.delete(key)
        instance.delete()

    @action(detail=False, methods=['post'])
    def create_with_data(self, request):
        """
        Создание аудитории с характеристиками и изображениями.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            # Инвалидируем кеш списка
            cache.delete("api_audiences_list")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def update_with_data(self, request, pk=None):
        """
        Полное обновление аудитории с характеристиками и изображениями.
        """
        audience = self.get_object()
        serializer = self.get_serializer(audience, data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            # Инвалидируем кеш объекта и списка
            for key in self.get_cache_keys(instance):
                cache.delete(key)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)