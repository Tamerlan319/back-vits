from rest_framework import views, status, viewsets, generics
from .models import Group, User, PhoneVerification, PhoneConfirmation, Appeal, AppealResponse
from .serializers import (
    UserSerializer, GroupSerializer, AuthorizationSerializer, 
    PhoneLoginSerializer, PhoneVerifySerializer, RegisterInitSerializer, 
    RegisterConfirmSerializer, AppealSerializer, AppealResponseSerializer,
    NotificationSerializer
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

class RegisterInitView(views.APIView):
    def post(self, request):
        serializer = RegisterInitSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
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
                    'password': data['password']
                }
            )
            
            # В реальном приложении здесь отправка SMS
            print(f"Код подтверждения для {data['phone']}: {code}")

            # # Форматируем номер телефона для Textbelt (международный формат)
            # phone_number = f"+7{data['phone'][1:]}"  # Преобразуем 79536428046 в +79536428046
            
            # # Отправка SMS через Textbelt
            # try:
            #     resp = requests.post(
            #         'https://textbelt.com/text',
            #         {
            #             'phone': phone_number,
            #             'message': f'Ваш код подтверждения: {code}',
            #             'key': 'textbelt',
            #         },
            #         timeout=10  # Таймаут 10 секунд
            #     )
            #     resp_data = resp.json()
            #     print(f"Ответ от Textbelt: {resp_data}")
                
            #     if not resp_data.get('success'):
            #         print(f"Ошибка отправки SMS: {resp_data.get('error')}")
            #         # В случае ошибки продолжаем работу, но логируем проблему
            # except Exception as e:
            #     print(f"Ошибка при отправке запроса к Textbelt: {str(e)}")
            #     # Продолжаем работу даже при ошибке отправки SMS
            
            return Response({
                "status": "success",
                "message": "Код подтверждения отправлен",
                "phone": data['phone'],
                "next_step": "confirm_code"
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterConfirmView(views.APIView):
    def post(self, request):
        serializer = RegisterConfirmSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            confirmation = data['confirmation']
            reg_data = confirmation.registration_data
            
            # Создаем пользователя
            user = User.objects.create_user(
                username=reg_data['username'],
                phone=confirmation.phone,
                first_name=reg_data['first_name'],
                last_name=reg_data['last_name'],
                password=reg_data['password'],
                phone_verified=True
            )
            
            # Удаляем запись подтверждения
            confirmation.delete()
            
            # # Генерируем токены
            # refresh = RefreshToken.for_user(user)
            
            return Response({
                "status": "success",
                "message": "Регистрация завершена",
                # "tokens": {
                #     "refresh": str(refresh),
                #     "access": str(refresh.access_token)
                # },
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "phone": str(user.phone)
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuthorizationView(views.APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'phone': str(user.phone)
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], serializer_class=RegisterInitSerializer)
    def register(self, request):
        """
        Регистрация нового пользователя.
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Генерация токена подтверждения
            token = generate_confirmation_token(user.email)
            
            # Создание ссылки для подтверждения
            confirmation_url = request.build_absolute_uri(
                reverse('confirm_email', args=[token]))
            
            # Отправка письма
            send_mail(
                'Подтвердите ваш email',
                f'Перейдите по ссылке для подтверждения: {confirmation_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({"message": "Письмо с подтверждением отправлено на ваш email."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def confirm_email(self, request, token):
        """
        Подтверждение email.
        """
        email = confirm_token(token)
        if not email:
            return Response({"error": "Недействительная или истекшая ссылка подтверждения."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(email=email)
        
        if user.is_active:
            return Response({"message": "Email уже подтвержден."}, status=status.HTTP_200_OK)
        
        # Активируем пользователя
        user.is_active = True
        user.save()
        
        return Response({"message": "Email успешно подтвержден."}, status=status.HTTP_200_OK)

class PhoneLoginView(APIView):
    def post(self, request):
        serializer = PhoneLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'phone': str(user.phone)
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendVerificationCodeView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response(
                {"error": "Укажите номер телефона"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Удаляем все нецифровые символы и добавляем + в начале
        phone = '+' + ''.join(filter(str.isdigit, phone))

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, не запрашивали ли код недавно
        last_code = PhoneVerification.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).first()

        if last_code:
            return Response(
                {"error": "Повторный код можно запросить через 1 минуту"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Генерируем 6-значный код
        code = str(random.randint(100000, 999999))

        # Сохраняем код в базу
        PhoneVerification.objects.create(
            user=user,
            code=code,
            is_used=False
        )

        # Если DEBUG=True, выводим код в консоль (для тестов)
        if settings.DEBUG:
            print(f"\n🔴 Код подтверждения для {phone}: {code}\n")
            return Response(
                {"message": "Код отправлен (тестовый режим)", "code": code},
                status=status.HTTP_200_OK
            )

        # Отправляем SMS через Textbelt
        try:
            response = requests.post(
                'https://textbelt.com/text',
                {
                    'phone': phone,
                    'message': f'Ваш код подтверждения: {code}',
                    'key': 'textbelt'  # Бесплатный ключ (лимит 1 SMS/день)
                }
            )
            data = response.json()

            if data.get('success'):
                return Response(
                    {"message": "Код отправлен на ваш телефон"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": f"Ошибка Textbelt: {data.get('error', 'Unknown error')}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return Response(
                {"error": f"Ошибка при отправке SMS: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

class AppealViewSet(viewsets.ModelViewSet):
    queryset = Appeal.objects.all()
    serializer_class = AppealSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'teacher']:
            return Appeal.objects.all()
        return Appeal.objects.filter(user=user)
    
    def perform_create(self, serializer):
        appeal = serializer.save(user=self.request.user)
        # Создаем уведомление для администраторов
        admins = User.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                appeal=appeal,
                notification_type='appeal_created',
                message=f'Новое обращение от {self.request.user.username}: {appeal.title}'
            )

class AppealResponseViewSet(viewsets.ModelViewSet):
    queryset = AppealResponse.objects.all()
    serializer_class = AppealResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'teacher']:
            return AppealResponse.objects.all()
        return AppealResponse.objects.filter(appeal__user=user)
    
    def perform_create(self, serializer):
        response = serializer.save(admin=self.request.user)
        appeal = response.appeal
        
        # Обновляем статус обращения, если это первый ответ
        if appeal.status == 'new':
            appeal.status = 'in_progress'
            appeal.save()
        
        # Создаем уведомление для пользователя
        Notification.objects.create(
            user=appeal.user,
            appeal=appeal,
            notification_type='appeal_response',
            message=f'Получен ответ на ваше обращение "{appeal.title}"'
        )

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)