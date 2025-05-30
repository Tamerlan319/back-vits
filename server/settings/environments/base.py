"""
Django settings for mystepik project.

Generated by 'django-admin startproject' using Django 4.2.20.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Основные настройки Yandex Cloud S3
AWS_ACCESS_KEY_ID = 'YCAJEsXZW5hb-D0ezzq8z1in-'  # IAM-ключ
AWS_SECRET_ACCESS_KEY = 'YCPJ5w6vwQIX_OhDd0i5UsmTiAixbfHRnhY337Zw'  # IAM-секрет
AWS_S3_ENDPOINT_URL = 'https://storage.yandexcloud.net'
AWS_S3_REGION_NAME = 'ru-central1'
AWS_S3_SIGNATURE_VERSION = 's3v4'

# Публичный бакет (для статики/медиа)
AWS_STORAGE_BUCKET_NAME = 'vits'  # Имя публичного бакета
AWS_DEFAULT_ACL = 'public-read'  # Файлы доступны без авторизации
AWS_QUERYSTRING_AUTH = False  # Не требовать подписи URL

# Приватный бакет (для документов)
PRIVATE_AWS_STORAGE_BUCKET_NAME = 'vits-private'  # Имя приватного бакета
PRIVATE_AWS_DEFAULT_ACL = 'private'  # Доступ только по подписи
PRIVATE_AWS_QUERYSTRING_AUTH = True  # Генерировать подписанные URL

# Пути для загрузки файлов
PUBLIC_MEDIA_LOCATION = 'media'  # Папка в публичном бакете
PRIVATE_MEDIA_LOCATION = 'protected'  # Папка в приватном бакете

# VK OAuth 2.1https://www.pythonanywhere.com/user/Tamik327/files/home/Tamik327/back-vits/server/settings
VK_CLIENT_ID = '53621398'
VK_CLIENT_SECRET = 'd99d7316d99d7316d99d731615daaf4180dd99dd99d7316b1ae015d6901a7ff146ec7fe'
VK_REDIRECT_URI = 'https://9d6f344add41e2f82cb50c416a06156c.serveo.net/auth/vk/callback/'
VK_API_VERSION = '5.199'
VK_AUTH_URL = "https://id.vk.com/authorize"
VK_TOKEN_URL = "https://id.vk.com/oauth2/auth"  # Ключевое изменение!
VK_SCOPE = 'email,phone'  # Только необходимые scope
FRONT_VK_CALLBACK = 'https://tamik.surge.sh/'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

TEXTBELT_API_KEY = 'e6a38bb90671d42125a40bf555da81c5315ca7aabUUwHB9Ff83lVU8sJzGc0T5Qf'  # Для платной версии

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-3zyo8&mht8vs9q-1dcfc74zzuw55_zsbudgcr4^k2m4g1pnz(a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Настройки SMS.RU
SMSRU_API_KEY = '0D3B2BC8-BB00-062A-3496-E40613279A32'  # Например, '12345678-ABCD-4321-5678-9876543210'
SMSRU_SENDER = 'VITS'  # Имя отправителя (должно быть заранее зарегистрировано в sms.ru)

# Настройки для Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # Схема для автоматической генерации API-документации
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'EXCEPTION_HANDLER': 'server.apps.news.exceptions.custom_exception_handler',
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = '@gmail.com'  # Ваш Gmail
EMAIL_HOST_PASSWORD = ''  # Пароль от Gmail или пароль приложения
DEFAULT_FROM_EMAIL = '@gmail.com'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Настройки для drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'User Management API',                               # Название API
    'DESCRIPTION': 'API для регистрации, получения и удаления пользователей.',  # Описание API
    'VERSION': '1.0.0',                                           # Версия API
    'SERVE_INCLUDE_SCHEMA': False,                                # Отключение схемы в ответах API
}

DEBUG_SOCKETS = True  # Флаг для включения/выключения WebSockets

if DEBUG_SOCKETS:
    ASGI_APPLICATION = 'server.asgi.application'
    
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [('127.0.0.1', 6379)],
            },
        },
    }

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Настройки микросервиса групп
GROUP_SERVICE_URL = 'http://127.0.0.1:8000'  # или ваш URL
SERVICE_AUTH_TOKEN = 'dev-internal-token'  # Общий для всех внутренних сервисов

INSTALLED_APPS = [
    'server.apps.Application',
    'server.apps.Content',
    'debug_toolbar',
    'phonenumber_field',
    'django_filters',
    'server.apps.proftesting',
    'server.apps.perscalendar',
    'server.apps.directions',
    'server.apps.news',
    'channels',
    'corsheaders',
    'server.apps.virtmuseum',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'server.apps.users',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

PHONENUMBER_DEFAULT_REGION = 'RU'

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ---------------------------------

CORS_ALLOW_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://26.152.2.215:5173"
]

CORS_ALLOW_ALL_ORIGINS = True

ALLOWED_HOSTS = ['*']

# Разрешаем cookies и авторизацию
CORS_ALLOW_CREDENTIALS = True

# Разрешаем все методы (GET, POST, PUT и т.д.)
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# ---------------------------------

ROOT_URLCONF = 'server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'server.wsgi.application'

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # 'server.apps.users.backends.EmailBackend',
    # 'server.apps.users.backends.PhoneBackend',  # Аутентификация по телефону
]

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",  # Теперь Redis в Docker!
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#         "KEY_PREFIX": "events_service"
#     }
# }

# Время жизни кеша по умолчанию (в секундах)
CACHE_TTL = 60 * 0.1  # 1 минут

INTERNAL_IPS = ['127.0.0.1']

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,  # Принудительно показывать панель
}