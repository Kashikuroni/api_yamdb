from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

router_v1 = DefaultRouter()
router_v1.register('titles', views.TitleViewSet, basename='title')
router_v1.register('categories', views.CategoryViewSet, basename='category')
router_v1.register('genres', views.GenreViewSet, basename='genre')
router_v1.register('auth/signup', views.SignUpViewSet, basename='signup')
router_v1.register('users', views.UserViewSet, basename='users')

urlpatterns = [
    path('v1/users/me/', views.UserMeAPIView.as_view(), name='user-me'),
    path('v1/auth/token/',
         views.ObtainTokenAPIView.as_view(),
         name='obtain_token'),
    path('v1/', include(router_v1.urls)),
]
