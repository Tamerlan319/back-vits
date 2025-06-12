from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from server.apps.users.views import (
    GroupView, 
    UserView, 
    AuthorizationView, 
    # PhoneLoginView, 
    VerifyPhoneView,
    RegisterInitView, 
    RegisterConfirmView,
    VKAuthInitView,
    VKAuthCallbackView,
    AdminUserListView,
    AdminUserDetailView,
    AdminUserBlockView,
    AdminUserUnblockView,
    AdminUserStatsView
)
from server.apps.virtmuseum.views import AudienceViewSet, AudienceImageViewSet, CharacteristicViewSet #представления из сериса виртуального музея
from server.apps.news.views import (
    CategoryViewSet, TagViewSet, NewsViewSet, 
    CommentViewSet, LikeViewSet
)#представления из сервиса новостей
from server.apps.directions.views import DepartmentViewSet, ProgramViewSet
from server.apps.perscalendar.views import EventViewSet
from server.apps.proftesting.views import (
    EducationLevelsView,
    QuestionGroupsView,
    QuestionsView,
    StartTestView,
    SubmitAnswerView,
    CompleteTestView,
    TestResultView
)
from server.apps.Content.views import BannerViewSet, AchievementViewSet, ReviewViewSet, OrganizationDocumentViewSet, VideoContentViewSet
from server.apps.Application.views import ApplicationViewSet, ApplicationAttachmentViewSet, get_application_types
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r'api/groups', GroupView, basename='group')
router.register(r'api/users', UserView, basename='users') 
router.register(r'api/audiences', AudienceViewSet, basename='audience')
router.register(r'api/categories', CategoryViewSet, basename='categories') 
router.register(r'api/tags', TagViewSet, basename='tags')
router.register(r'api/news', NewsViewSet, basename='news')
router.register(r'api/news/latest_news', NewsViewSet, basename='latest_news') 
router.register(r'api/comments', CommentViewSet, basename='comments')
router.register(r'api/likes', LikeViewSet, basename='likes') 
router.register(r'api/audience-images', AudienceImageViewSet, basename='audience-images')
router.register(r'api/characteristics', CharacteristicViewSet, basename='characteristics')
router.register(r'api/departments', DepartmentViewSet, basename='departments')
router.register(r'api/programs', ProgramViewSet, basename='programs')
router.register(r'api/banners', BannerViewSet, basename='banner')
router.register(r'api/achievements', AchievementViewSet, basename='achievement')
router.register(r'api/reviews', ReviewViewSet, basename='review')
router.register(r'api/documents', OrganizationDocumentViewSet, basename='documents')
router.register(r'api/videos', VideoContentViewSet, basename='videos')
router.register(r'api/events', EventViewSet, basename='events')
router.register(r'api/applications', ApplicationViewSet, basename='application')
router.register(r'api/application-attachments', ApplicationAttachmentViewSet, basename='application-attachment')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('__debug__/', include('debug_toolbar.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/init/', RegisterInitView.as_view(), name='register-init'),
    path('api/register/confirm/', RegisterConfirmView.as_view(), name='register-confirm'),
    path('api/login/', AuthorizationView.as_view(), name='login'),
    # path('api/login/phone/', PhoneLoginView.as_view(), name='phone_login'),
    path('api/question-groups/', QuestionGroupsView.as_view(), name='question-groups'),
    path('api/questions/', QuestionsView.as_view(), name='questions'),
    path('api/start-test/', StartTestView.as_view(), name='start-test'),
    path('api/sessions/<int:session_id>/answers/', SubmitAnswerView.as_view(), name='submit-answers'),
    path('api/sessions/<int:session_id>/complete/', CompleteTestView.as_view(), name='complete-test'),
    path('api/results/<int:session_id>/', TestResultView.as_view(), name='test-result'),
    path('auth/vk/init/', VKAuthInitView.as_view(), name='vk-auth-init'),
    path('auth/vk/callback/', VKAuthCallbackView.as_view(), name='vk-auth-callback'),
    path('api/application-types/', get_application_types, name='application-types'),
    path('api/admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('api/admin/users/<uuid:uuid>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('api/admin/users/<uuid:uuid>/block/', AdminUserBlockView.as_view(), name='admin-user-block'),
    path('api/admin/users/<uuid:uuid>/unblock/', AdminUserUnblockView.as_view(), name='admin-user-unblock'),
    path('api/admin/stats/', AdminUserStatsView.as_view(), name='admin-stats'),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)