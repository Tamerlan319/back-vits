from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action   
from .models import Audience, Characteristic, AudienceImage
from .serializers import AudienceCreateUpdateSerializer, CharacteristicCreateSerializer, AudienceImageCreateSerializer

class AudienceImageViewSet(viewsets.ModelViewSet):
    queryset = AudienceImage.objects.all()
    serializer_class = AudienceImageCreateSerializer

class CharacteristicViewSet(viewsets.ModelViewSet):
    queryset = Characteristic.objects.all()
    serializer_class = CharacteristicCreateSerializer

class AudienceViewSet(viewsets.ModelViewSet):
    queryset = Audience.objects.all()
    serializer_class = AudienceCreateUpdateSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AudienceCreateUpdateSerializer
        return AudienceCreateUpdateSerializer

    @action(detail=False, methods=['post'])
    def create_with_data(self, request):
        """
        Создание аудитории с характеристиками и изображениями.
        """
        serializer = AudienceCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def update_with_data(self, request, pk=None):
        """
        Полное обновление аудитории с характеристиками и изображениями.
        """
        audience = self.get_object()
        serializer = AudienceCreateUpdateSerializer(audience, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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