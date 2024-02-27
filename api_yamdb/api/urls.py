from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignUpViewSet, ObtainTokenAPIView, UserViewSet

router_v1 = DefaultRouter()
router_v1.register('titles', TitleViewSet, basename='title')
router_v1.register('categories', CategoryViewSet, basename='category')
router_v1.register('genres', GenreViewSet, basename='genre')
router_v1.register(r'auth/signup', SignUpViewSet, basename='signup')
# router_v1.register(r'auth/token', ObtainTokenAPIView, basename='obtain-token')
router_v1.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/auth/token/', ObtainTokenAPIView.as_view(), name='obtain_token')
    # Другие маршруты вашего приложения...
]