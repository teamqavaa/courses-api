from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("auth/login/", views.login, name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/", views.register, name="users-register"),
    path("users/me/", views.me, name="users-me"),
    path("admin/users/bulk/", views.admin_users_bulk, name="admin_users_bulk"),
    path("admin/users/", views.admin_users, name="admin_users"),
    path("admin/users/<uuid:pk>/", views.admin_user, name="admin_user"),
]
