from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignUpViewSet,
    ObtainTokenAPIView,
    UserViewSet,
    UserMeAPIView
)

router_v1 = DefaultRouter()
router_v1.register(r'auth/signup', SignUpViewSet, basename='signup')
router_v1.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('v1/users/me/', UserMeAPIView.as_view(), name='user-me'),
    path('v1/auth/token/', ObtainTokenAPIView.as_view(), name='obtain_token'),
    path('v1/', include(router_v1.urls)),
    # Другие маршруты вашего приложения...
]
