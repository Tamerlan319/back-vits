from rest_framework import views, status, viewsets, generics, permissions
from .models import Group, User, PhoneConfirmation, UserActivityLog, UserPhone
from .serializers import (
    UserSerializer, GroupSerializer, AuthorizationSerializer,
    PhoneLoginSerializer, RegisterInitSerializer,
    RegisterConfirmSerializer, VKAuthSerializer, AdminUserListSerializer,
    AdminUserDetailSerializer, AdminUserUpdateSerializer, UserSearchSerializer
)
from rest_framework.views import APIView
from .utils import generate_confirmation_token, confirm_token
from django.conf import settings
from django.urls import reverse
from django.core.mail import send_mail
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
import random
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from datetime import timedelta
from django.utils import timezone
import requests
from urllib.parse import urlencode
import secrets
import base64
import hashlib
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from urllib.parse import urlparse, parse_qs, urlunparse
import os
from django.core.files.base import ContentFile

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from rest_framework import serializers
from .models import User, Group, PhoneConfirmation, UserPhone
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random
import phonenumbers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import User, UserActivityLog
from django.utils.translation import gettext_lazy as _
import base64
import hashlib
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

class TokenRefreshView(APIView):
    def post(self, request):
        # Get refresh token from cookies
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is missing in cookies.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create serializer and validate data
            serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)
            
            # Get new tokens
            new_access_token = serializer.validated_data.get('access')
            new_refresh_token = serializer.validated_data.get('refresh')
            
            response_data = {
                'access': new_access_token,
            }
            
            response = Response(response_data)
            
            # Update refresh token in cookie
            if new_refresh_token:
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                    value=new_refresh_token,
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
                )
            
            return response
            
        except TokenError as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

def generate_pkce():
    """Генерация code_verifier и code_challenge для PKCE"""
    code_verifier = secrets.token_urlsafe(96)
    code_verifier = ''.join([c for c in code_verifier if c.isalnum() or c in {'-', '.', '_', '~'}])[:128]

    if len(code_verifier) < 43:
        code_verifier += secrets.token_urlsafe(43 - len(code_verifier))

    sha256 = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256).decode('ascii').replace('=', '')

    return code_verifier, code_challenge

class VKAuthInitView(APIView):
    def get(self, request):
        """Инициирует авторизацию через VK (перенаправление)"""
        try:
            code_verifier, code_challenge = generate_pkce()
            state = secrets.token_urlsafe(32)

            request.session['vk_code_verifier'] = code_verifier
            request.session['vk_state'] = state

            params = {
                'client_id': settings.VK_CLIENT_ID,
                'redirect_uri': settings.VK_REDIRECT_URI,
                'response_type': 'code',
                'scope': settings.VK_SCOPE,
                'state': state,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',
                'v': settings.VK_API_VERSION,
            }

            auth_url = f"{settings.VK_AUTH_URL}?{urlencode(params)}"
            return redirect(auth_url)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VKAuthCallbackView(APIView):
    def get(self, request):
        """Обрабатывает callback от VK"""
        code = request.GET.get('code')
        error = request.GET.get('error')
        state = request.GET.get('state')

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        if not code:
            return Response({"error": "Authorization code not provided"},
                          status=status.HTTP_400_BAD_REQUEST)

        # Проверяем state
        saved_state = request.session.get('vk_state')
        if state != saved_state:
            return Response({"error": "Invalid state parameter"},
                          status=status.HTTP_400_BAD_REQUEST)

        code_verifier = request.session.get('vk_code_verifier')
        if not code_verifier:
            return Response({"error": "Code verifier not found"},
                          status=status.HTTP_400_BAD_REQUEST)

        device_id = request.GET.get('device_id', '')

        # Получаем токен от VK
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': settings.VK_CLIENT_ID,
            'redirect_uri': settings.VK_REDIRECT_URI,
            'code': code,
            'code_verifier': code_verifier,
            'device_id': device_id
        }

        try:
            # Отправляем запрос к VK API
            response = requests.post(
                "https://id.vk.com/oauth2/auth",
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code != 200:
                error_msg = response.json().get('error_description', 'VK API error')
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

            token_info = response.json()

            # Создаем или получаем пользователя
            user, created = User.objects.get_or_create(
                vk_id=token_info['user_id'],
                defaults={
                    'username': f"vk_{token_info['user_id']}",
                    'is_active': True,
                    'phone_verified': True
                }
            )

            # Обновляем данные пользователя из VK
            if 'access_token' in token_info:
                try:
                    # Получаем данные пользователя через новый endpoint
                    vk_response = requests.post(
                        "https://id.vk.com/oauth2/user_info",
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded'
                        },
                        data={
                            'access_token': token_info['access_token'],
                            'client_id': settings.VK_CLIENT_ID,
                            'v': settings.VK_API_VERSION
                        }
                    )

                    print("VK User Info Response:", vk_response.json())  # Логируем ответ

                    username_response = requests.get(
                        "https://api.vk.com/method/account.getProfileInfo",
                        params={
                            'access_token': token_info['access_token'],
                            'v': settings.VK_API_VERSION,
                            'fields': 'screen_name'
                        }
                    )
                    
                    if username_response.status_code == 200:
                        vk_data_username = username_response.json().get('response', [{}])

                    if vk_response.status_code == 200:
                        vk_data = vk_response.json().get('user', {})

                        # Обновление данных пользователя
                        update_fields = {}
                        if vk_data.get('first_name'):
                            user.first_name = vk_data['first_name']
                            update_fields['first_name'] = vk_data['first_name']

                        if vk_data.get('last_name'):
                            user.last_name = vk_data['last_name']
                            update_fields['last_name'] = vk_data['last_name']

                        if vk_data.get('phone'):
                            # Обновляем телефон через UserPhone
                            phone_str = vk_data['phone']
                            if not hasattr(user, 'phone_data'):
                                UserPhone.objects.create(user=user, phone=phone_str)
                            else:
                                user.phone_data.phone = phone_str
                                user.phone_data.save()
                            
                            user.phone_verified = True
                            update_fields['phone_verified'] = True

                        if vk_data.get('email'):
                            user.email = vk_data['email']
                            update_fields['email'] = vk_data["email"]

                        if vk_data_username.get('screen_name'):
                            user.username = vk_data_username['screen_name']

                        # Установка аватара из URL
                        if vk_data.get('avatar'):
                            avatar_url = vk_data['avatar']
                            try:
                                avatar_response = requests.get(avatar_url)
                                if avatar_response.status_code == 200:
                                    parsed_url = urlparse(avatar_url)
                                    filename = os.path.basename(parsed_url.path)
                                    user.avatar.save(
                                        filename,
                                        ContentFile(avatar_response.content),
                                        save=False  # Не сохраняем пока
                                    )
                                    update_fields['avatar'] = 'from_vk'
                            except Exception as e:
                                print("Ошибка при загрузке аватара:", str(e))

                        # Дополнительные поля
                        user.role = "guest"
                        user.is_active = True

                        user.save()

                except Exception as e:
                    print(f"Error getting user info from VK: {str(e)}")

            # Генерируем JWT токены
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Создаем редирект-ответ
            redirect_url = f"{settings.FRONT_VK_CALLBACK}?access={access_token}&user_id={user.id}&username={user.username}"
            
            # Добавляем phone и email если они есть
            if hasattr(user, 'phone') and user.phone:
                redirect_url += f"&phone={user.phone}"
            if user.email:
                redirect_url += f"&email={user.email}"

            response = redirect(redirect_url)
            
            # Устанавливаем refresh token в куки (если USE_JWT_COOKIES=True)
            if settings.USE_JWT_COOKIES:
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                    value=refresh_token,
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
                )
            
            return response

        except requests.exceptions.RequestException as e:
            return Response({"error": f"VK API request failed: {str(e)}"},
                          status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"},
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GroupView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get']

class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'head', 'options']

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def me(self, request):
        """Получение информации о текущем пользователе"""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Не предоставлены данные для аутенфикации."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

import json
import logging

logger = logging.getLogger(__name__)

class RegisterInitView(views.APIView):
    def post(self, request):
        serializer = RegisterInitSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Проверяем существование телефона через хеш
            phone_str = str(data['phone'])
            phone_hash = hashlib.sha256(phone_str.encode()).hexdigest()
            
            # Проверка существующего UserPhone
            if UserPhone.objects.filter(phone_hash=phone_hash).exists():
                return Response(
                    {"phone": "Этот номер уже зарегистрирован"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Удаляем старые подтверждения для этого номера
            PhoneConfirmation.objects.filter(phone=data['phone']).delete()
            
            # Генерируем код
            code = str(random.randint(100000, 999999))
            
            # Сохраняем данные для подтверждения
            PhoneConfirmation.objects.create(
                phone=data['phone'],
                code=code,
                registration_data={
                    'username': data['username'],
                    'first_name': data.get('first_name', ''),
                    'last_name': data.get('last_name', ''),
                    'middle_name': data.get('middle_name', ''),
                    'password': data['password']
                }
            )
            
            # # Отправка SMS
            self._send_sms_via_exolve(data['phone'], code)
                
            return Response({
                "status": "success",
                "message": "Код подтверждения отправлен",
                "phone": phone_str,
                "next_step": "confirm_code"
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_sms_via_exolve(self, phone, code):
        """Отправка SMS через Exolve API"""
        url = "https://api.exolve.ru/messaging/v1/SendSMS"
        
        # Нормализация номера телефона
        cleaned_phone = ''.join(filter(str.isdigit, str(phone)))
        if cleaned_phone.startswith('8'):
            cleaned_phone = '7' + cleaned_phone[1:]
        elif not cleaned_phone.startswith('7'):
            cleaned_phone = '7' + cleaned_phone
        print(f"Номер отправки {cleaned_phone}")
        code_spaced = " ".join(list(str(code)))
        # Формируем текст сообщения
        text = f"Ваш проверочный код: {code_spaced}. Никому не сообщайте этот код. С уважением, Высшая ИТ-школа."
        
        # Подготовка данных для запроса
        payload = {
            "number": settings.EXOLVE_SENDER_NAME,  # Ваш номер отправителя из примера
            "destination": cleaned_phone,
            "text": text
        }
        
        headers = {
            "Authorization": "Bearer " + settings.EXOLVE_API_KEY,  # Ваш токен из примера
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            response_data = response.json()
            if 'message_id' in response_data:
                return True
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке SMS: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Детали ошибки: {e.response.text}")
            raise Exception("Не удалось отправить SMS. Пожалуйста, попробуйте позже.")

class RegisterConfirmView(views.APIView):
    def post(self, request):
        serializer = RegisterConfirmSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            confirmation = data['confirmation']
            reg_data = confirmation.registration_data

            # Нормализуем телефон (убедитесь, что он в формате "+7...")
            phone_str = str(confirmation.phone)
            phone_hash = hashlib.sha256(phone_str.encode()).hexdigest()

            user = User.objects.create_user(
                username=reg_data['username'],
                first_name=reg_data.get('first_name', ''),
                last_name=reg_data.get('last_name', ''),
                middle_name=reg_data.get('middle_name', ''),
                password=reg_data['password'],
                phone_verified=True,
                is_active=True,
                is_verified = True,
                role='guest'
            )

            # Создаём UserPhone с phone_hash и encrypted_phone
            UserPhone.objects.create(
                phone_hash=phone_hash,
                phone=phone_str  # Вызовет phone.setter, который зашифрует номер
            )

            confirmation.delete()
            return Response({
                "status": "success",
                "message": "Регистрация завершена",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "is_active": user.is_active,
                    "phone_verified": user.phone_verified
                }
            })
        return Response(serializer.errors, status=400)

class AuthorizationView(APIView):
    def post(self, request):
        serializer = AuthorizationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Проверка блокировки пользователя
            if user.is_blocked:
                blocked_info = {
                    'error': 'Пользователь заблокирован',
                    'is_blocked': True,
                    'blocked_at': user.blocked_at,
                    'blocked_reason': user.blocked_reason,
                    'blocked_by': user.blocked_by.username if user.blocked_by else None
                }
                return Response(blocked_info, status=status.HTTP_403_FORBIDDEN)
            
            # Проверка верификации (если требуется)
            if not user.is_verified:
                return Response(
                    {'error': 'Аккаунт не верифицирован'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Генерация токенов
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            response_data = {
                'access': access_token,
                'user_id': user.id,
                'username': user.username,
                'phone': str(user.phone) if user.phone else None,
                'role': user.role,
                'is_verified': user.is_verified,
                'is_blocked': user.is_blocked  # Для информации, всегда False здесь
            }
            
            response = Response(response_data)
            
            # Добавляем refresh token в куки если нужно
            if getattr(settings, 'USE_JWT_COOKIES', False):
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                    value=refresh_token,
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
                )
            else:
                response_data['refresh'] = refresh_token
            
            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PhoneLoginView(APIView):
    def post(self, request):
        serializer = PhoneLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            response_data = {
                'access': access_token,
                'user_id': user.id,
                'username': user.username,
                'phone': user.phone
            }
            
            response = Response(response_data)
            
            # Добавляем refresh token в куки только если USE_JWT_COOKIES=True
            if settings.USE_JWT_COOKIES:
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                    value=refresh_token,
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
                )
            else:
                # В режиме разработки отправляем refresh token в теле ответа
                response_data['refresh'] = refresh_token
            
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyPhoneView(APIView):
    def post(self, request):
        serializer = PhoneVerifySerializer(data=request.data)
        if serializer.is_valid():
            verification = serializer.validated_data['verification']
            user = verification.user

            # Активируем пользователя и подтверждаем телефон
            user.is_active = True
            user.phone_verified = True
            user.save()

            # Помечаем код как использованный
            verification.is_used = True
            verification.save()

            return Response({"message": "Телефон успешно подтвержден"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

class IsAdminRole(permissions.BasePermission):
    """
    Доступ только пользователям с ролью 'admin'
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser, IsAdminRole]
    pagination_class = AdminUserPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active', 'is_blocked']
    
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')

class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser, IsAdminRole]
    lookup_field = 'uuid'
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AdminUserDetailSerializer
        return AdminUserUpdateSerializer
    
    def perform_update(self, serializer):
        user = serializer.save()
        request = self.request
        
        # Логирование изменений
        changes = {}
        for field, value in serializer.validated_data.items():
            if getattr(user, field) != value:
                changes[field] = {
                    'old': getattr(user, field),
                    'new': value
                }
        
        if changes:
            UserActivityLog.objects.create(
                user=user,
                action='profile_update',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                metadata={
                    'changed_by': str(request.user.uuid),
                    'changes': changes
                }
            )

class AdminUserBlockView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser, IsAdminRole]
    lookup_field = 'uuid'
    
    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response(
                {'detail': _('Block reason is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.block(reason, request.user)
        
        # Логирование блокировки
        UserActivityLog.objects.create(
            user=user,
            action='block',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            metadata={
                'blocked_by': str(request.user.uuid),
                'reason': reason
            }
        )
        
        return Response(
            {'status': _('User blocked successfully')},
            status=status.HTTP_200_OK
        )

class AdminUserUnblockView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser, IsAdminRole]
    lookup_field = 'uuid'
    
    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        user.unblock()
        
        # Логирование разблокировки
        UserActivityLog.objects.create(
            user=user,
            action='unblock',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            metadata={
                'unblocked_by': str(request.user.uuid)
            }
        )
        
        return Response(
            {'status': _('User unblocked successfully')},
            status=status.HTTP_200_OK
        )

class AdminUserStatsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser, IsAdminRole]
    
    def get(self, request):
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        # Базовая статистика
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'blocked_users': User.objects.filter(is_blocked=True).count(),
            'users_by_role': User.objects.values('role').annotate(count=Count('id')),
        }
        
        # Статистика по регистрациям за последние 30 дней
        thirty_days_ago = timezone.now() - timedelta(days=30)
        registrations = (
            User.objects
            .filter(date_joined__gte=thirty_days_ago)
            .extra({'date': "date(date_joined)"})
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        stats['registrations_last_30_days'] = registrations
        
        return Response(stats)

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            response = Response({'detail': 'Successfully logged out.'})
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
            return response
            
        except Exception as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )