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
    PhoneLoginView, 
    SendVerificationCodeView, 
    VerifyPhoneView,
    RegisterInitView, 
    RegisterConfirmView,
    AppealViewSet,
    AppealResponseViewSet,
    NotificationViewSet, #представления из сервиса для работы с пользователями
    VKAuthInitView, VKAuthCallbackView
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
from server.apps.Content.views import BannerViewSet, AchievementViewSet, ReviewViewSet

router = routers.DefaultRouter()
router.register(r'api/groups', GroupView, basename='group') #получить список групп
# router.register(r'api/register', RegisterView, basename='register') #регистрация
router.register(r'api/users', UserView, basename='users') #получить список юзеров
router.register(r'api/audiences', AudienceViewSet, basename='audience') #получить список адуиторий
router.register(r'api/categories', CategoryViewSet, basename='categories') #категории новостей
router.register(r'api/tags', TagViewSet, basename='tags') #теги новостей
router.register(r'api/news', NewsViewSet, basename='news') #получить новости
router.register(r'api/news/latest_news', NewsViewSet, basename='latest_news') #получить последние три новости
router.register(r'api/comments', CommentViewSet, basename='comments') #комментарии
router.register(r'api/likes', LikeViewSet, basename='likes') #лайки
router.register(r'api/audience-images', AudienceImageViewSet, basename='audience-images') #получить фото аудиторий
router.register(r'api/characteristics', CharacteristicViewSet, basename='characteristics') #получить характеристики аудитории
router.register(r'api/departments', DepartmentViewSet, basename='departments') #получить направления обучения
router.register(r'api/programs', ProgramViewSet, basename='programs') #получить программы обучения
router.register(r'api/appeals', AppealViewSet, basename='appeal')
router.register(r'api/appeal-responses', AppealResponseViewSet, basename='appeal-response')
router.register(r'api/notifications', NotificationViewSet, basename='notification')
router.register(r'api/banners', BannerViewSet, basename='banner')
router.register(r'api/achievements', AchievementViewSet, basename='achievement')
router.register(r'api/reviews', ReviewViewSet, basename='review')
router.register(r'api/events', EventViewSet, basename='events')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/register', RegisterView.as_view(), name='register'), #регистрация
    # path('api/authorization/', AuthorizationView.as_view(), name='authorization'),
    path('api/register/init/', RegisterInitView.as_view(), name='register-init'),
    path('api/register/confirm/', RegisterConfirmView.as_view(), name='register-confirm'),
    path('api/authorization/', AuthorizationView.as_view(), name='login'),
    path('api/login/phone/', PhoneLoginView.as_view(), name='phone_login'),
    path('api/send-code/', SendVerificationCodeView.as_view(), name='send_code'),
    path('api/verify-phone/', VerifyPhoneView.as_view(), name='verify_phone'),
    path('api/education-levels/', EducationLevelsView.as_view(), name='education-levels'),
    path('api/question-groups/', QuestionGroupsView.as_view(), name='question-groups'),
    path('api/questions/', QuestionsView.as_view(), name='questions'),
    path('api/start-test/', StartTestView.as_view(), name='start-test'),
    path('api/sessions/<int:session_id>/answers/', SubmitAnswerView.as_view(), name='submit-answers'),
    path('api/sessions/<int:session_id>/complete/', CompleteTestView.as_view(), name='complete-test'),
    path('api/results/<int:session_id>/', TestResultView.as_view(), name='test-result'),
    path('auth/vk/init/', VKAuthInitView.as_view(), name='vk-auth-init'),
    path('auth/vk/callback/', VKAuthCallbackView.as_view(), name='vk-auth-callback'),
    path('__debug__/', include('debug_toolbar.urls')),  # дебаг для кеширования
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)