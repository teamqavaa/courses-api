# app/modules/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModuleViewSet

# Le router génère automatiquement toutes les routes standard pour le CRUD
# (GET, POST, PUT, PATCH, DELETE) ainsi que l'action personnalisée by_course
router = DefaultRouter()
router.register(r'modules', ModuleViewSet, basename='module')

urlpatterns = [
    path('', include(router.urls)),
]
