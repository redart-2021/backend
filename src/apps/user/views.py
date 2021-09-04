from django.contrib.auth import authenticate, login
from rest_framework import (
    generics,
    mixins,
    permissions,
    viewsets,
)
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser
from .serializers import (
    CustomTokenObtainSerializer,
    LoginSerializer,
    ProfileSerializer,
    RegistrationSerializer,
    UserSerializer,
)

__all__ = ['CustomTokenObtainView', 'RegistrationView', 'LoginView', 'ProfileView']


class CustomTokenObtainView(TokenObtainPairView):
    serializer_class = CustomTokenObtainSerializer


class RegistrationView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegistrationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if not user:
            raise ValidationError('Неверный пользователь или пароль', code='invalid_credentials')
        if not user.is_active:
            raise ValidationError('Пользователь заблокирован', code='inactive')

        login(request, user)
        return Response()


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


class UsersViewSet(viewsets.GenericViewSet,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin):
    model = CustomUser
    queryset = model.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ('position',)
    search_fields = ('first_name', 'last_name', 'middle_name')
