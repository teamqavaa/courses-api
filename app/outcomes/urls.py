# app/outcomes/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseOutcomeViewSet

# Le router génère automatiquement toutes les routes standard pour le CRUD
# (GET, POST, PUT, PATCH, DELETE)
router = DefaultRouter()
router.register(r'course-outcomes', CourseOutcomeViewSet, basename='course-outcome')

urlpatterns = [
    path('', include(router.urls)),
]
