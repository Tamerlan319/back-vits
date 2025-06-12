from rest_framework import viewsets, permissions
from .models import Banner, Achievement, Review, OrganizationDocument, VideoContent
from .serializers import BannerSerializer, AchievementSerializer, ReviewSerializer, OrganizationDocumentSerializer, VideoContentSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsAdmin
from rest_framework import parsers

class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all().order_by('order')
    serializer_class = BannerSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdmin()]
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_destroy(self, instance):
        try:
            if instance.image:
                instance.image.delete()
            super().perform_destroy(instance)
        except Exception as e:
            print(f"Error deleting banner: {str(e)}")
            raise
    
    def destroy(self, request, *args, **kwargs):
        print(f"DELETE request for banner {kwargs.get('pk')}")
        print(f"User: {request.user}, Role: {getattr(request.user, 'role', None)}")
        return super().destroy(request, *args, **kwargs)

class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all().order_by('-created_at')
    serializer_class = AchievementSerializer
    permission_classes = [IsAdmin]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save()

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    queryset = Review.objects.all().order_by('-created_at')
    permission_classes = [IsAdmin]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save()

class OrganizationDocumentViewSet(viewsets.ModelViewSet):
    queryset = OrganizationDocument.objects.all()
    serializer_class = OrganizationDocumentSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdmin()]
    
    def perform_destroy(self, instance):
        try:
            if instance.file:
                instance.file.delete()
            super().perform_destroy(instance)
        except Exception as e:
            print(f"Ошибка при удалении документа: {str(e)}")
            raise

class VideoContentViewSet(viewsets.ModelViewSet):
    queryset = VideoContent.objects.all()
    serializer_class = VideoContentSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdmin()]