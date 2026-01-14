from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    MeView,
    RegisterView,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/jwt/create/", CustomTokenObtainPairView.as_view(), name="jwt-create"),
    path("auth/jwt/refresh/", CustomTokenRefreshView.as_view(), name="jwt-refresh"),
    path("auth/jwt/logout/", LogoutView.as_view(), name="jwt-logout"),
    path("users/me/", MeView.as_view(), name="users-me"),
    path("", include(router.urls)),
]
