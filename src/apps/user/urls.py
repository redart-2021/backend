from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import token_refresh, token_verify

from apps.user.views import (
    CustomTokenObtainView,
    LoginView,
    ProfileView,
    RegistrationView,
    UsersViewSet,
)

router = DefaultRouter()
router.register('users', UsersViewSet)

urlpatterns = [
    path('api/v1/registration/', RegistrationView.as_view(), name='registration'),
    path('api/v1/login/', LoginView.as_view(), name='login'),
    path('api/v1/token/', CustomTokenObtainView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', token_refresh, name='token_refresh'),
    path('api/v1/token/verify/', token_verify, name='token_verify'),
    path('api/v1/profile/', ProfileView.as_view(), name='profile'),
    path('api/v1/', include(router.urls)),
]
