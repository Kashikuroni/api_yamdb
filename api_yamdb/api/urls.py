from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignUpViewSet, ObtainTokenViewSet, UserViewSet

router_v1 = DefaultRouter()
router_v1.register(r'auth/signup', SignUpViewSet, basename='signup')
router_v1.register(r'auth/token', ObtainTokenViewSet, basename='obtain-token')
router_v1.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    # Другие маршруты вашего приложения...
]