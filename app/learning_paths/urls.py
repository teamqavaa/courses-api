# urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LearningPathViewSet

router = DefaultRouter()
router.register(r'learning-paths', LearningPathViewSet, basename='learningpath')

urlpatterns = [
    path('', include(router.urls)),
]
