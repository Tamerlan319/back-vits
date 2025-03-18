from rest_framework import status, viewsets, generics
from .models import Group, User
from .serializers import UserSerializer, GroupSerializer, RegisterSerializer, AuthorizationSerializer
from rest_framework.views import APIView
from .utils import generate_confirmation_token, confirm_token
from django.conf import settings
from django.urls import reverse
from django.core.mail import send_mail
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active')

class GroupView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get']

class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get']

class RegisterView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    http_method_names = ['post']

class AuthorizationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AuthorizationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], serializer_class=RegisterSerializer)
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