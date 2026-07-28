# app/courses/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet

# Le router génère automatiquement toutes les routes standard pour le CRUD
# (GET, POST, PUT, PATCH, DELETE)
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

urlpatterns = [
    path('', include(router.urls)),
]
