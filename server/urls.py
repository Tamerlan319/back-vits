from django.urls import path, include
from django.contrib import admin
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from server.apps.regapp.views import GroupView, RegisterView, UserView, AuthorizationView
#from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r'api/groups', GroupView, basename='group')
router.register(r'api/register', RegisterView, basename='register')
router.register(r'api/authorization', AuthorizationView, basename='authorization')
router.register(r'api/users', UserViewSet, basename='user')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #path('api/register/', RegisterView.as_view(), name='register'),
    #path('api/authorization/', AuthorizationView.as_view(), name='authorization'),
]