from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action   
from .models import Audience, Characteristic
from .serializers import AudienceSerializer, CharacteristicCreateSerializer

class AudienceViewSet(viewsets.ModelViewSet):
    queryset = Audience.objects.all()
    serializer_class = AudienceSerializer

    def update(self, request, *args, **kwargs):
        """
        Полное обновление аудитории.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Частичное обновление аудитории.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Удаление аудитории.
        """
        # Удаляем связанные характеристики
        instance.characteristics.all().delete()
        # Удаляем связанные изображения
        instance.images.all().delete()
        # Удаляем саму аудиторию
        instance.delete()

    @action(detail=True, methods=['post'])
    def add_characteristic(self, request, pk=None):
        """
        Добавление характеристики для аудитории.
        """
        audience = self.get_object()
        serializer = CharacteristicCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(audience=audience)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)