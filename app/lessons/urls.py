from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LessonViewSet

# Le router génère automatiquement toutes les routes standard pour le CRUD
# (GET, POST, PUT, PATCH, DELETE) ainsi que l'action personnalisée by_module
router = DefaultRouter()
router.register(r'lessons', LessonViewSet, basename='lesson')

urlpatterns = [
    path('', include(router.urls)),
]
