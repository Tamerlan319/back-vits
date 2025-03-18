from django.urls import path, include
from django.contrib import admin
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from server.apps.users.views import GroupView, RegisterView, UserViewSet, AuthorizationView #представления из сервиса для работы с пользователями
from server.apps.virtmuseum.views import AudienceViewSet

router = routers.DefaultRouter()
router.register(r'api/groups', GroupView, basename='group')
router.register(r'api/register', RegisterView, basename='register')
#router.register(r'api/authorization', AuthorizationView, basename='authorization')
router.register(r'api/users', UserViewSet, basename='user')
router.register(r'api/audiences', AudienceViewSet, basename='audience')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/authorization/', AuthorizationView.as_view(), name='authorization'),
    #path('api/authorization/', AuthorizationView.as_view(), name='authorization'),
]