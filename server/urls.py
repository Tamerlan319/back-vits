from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from server.apps.users.views import GroupView, RegisterView, UserViewSet, AuthorizationView #представления из сервиса для работы с пользователями
from server.apps.virtmuseum.views import AudienceViewSet, AudienceImageViewSet, CharacteristicViewSet #представления из сериса виртуального музея
from server.apps.news.views import (
    CategoryViewSet, TagViewSet, NewsViewSet, 
    CommentViewSet, LikeViewSet
)#представления из сервиса новостей

router = routers.DefaultRouter()
router.register(r'api/groups', GroupView, basename='group')
router.register(r'api/register', RegisterView, basename='register')
#router.register(r'api/authorization', AuthorizationView, basename='authorization')
router.register(r'api/users', UserViewSet, basename='user')
router.register(r'api/audiences', AudienceViewSet, basename='audience')
router.register(r'api/categories', CategoryViewSet, basename='categories')
router.register(r'api/tags', TagViewSet, basename='tags')
router.register(r'api/news', NewsViewSet, basename='news')
router.register(r'api/comments', CommentViewSet, basename='comments')
router.register(r'api/likes', LikeViewSet, basename='likes')
router.register(r'api/audience-images', AudienceImageViewSet, basename='audience-images')
router.register(r'api/characteristics', CharacteristicViewSet, basename='characteristics')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/authorization/', AuthorizationView.as_view(), name='authorization'),
    #path('api/authorization/', AuthorizationView.as_view(), name='authorization'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)