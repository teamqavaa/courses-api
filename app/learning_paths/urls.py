# urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .admin_views import (
    admin_path_outcome,
    admin_path_outcomes,
    admin_path_prerequisite,
    admin_path_prerequisites,
)
from .views import LearningPathViewSet

router = DefaultRouter()
router.register(r'learning-paths', LearningPathViewSet, basename='learningpath')

urlpatterns = [
    path('', include(router.urls)),
    path('learning-paths/<slug:path_slug>/outcomes/', admin_path_outcomes, name='admin-path-outcomes'),
    path('learning-paths/<slug:path_slug>/outcomes/<int:pk>/', admin_path_outcome, name='admin-path-outcome'),
    path('learning-paths/<slug:path_slug>/prerequisites/', admin_path_prerequisites, name='admin-path-prerequisites'),
    path('learning-paths/<slug:path_slug>/prerequisites/<int:pk>/', admin_path_prerequisite, name='admin-path-prerequisite'),
]
