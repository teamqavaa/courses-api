from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CourseRequirementViewSet

router = DefaultRouter()
router.register(r'requirements', CourseRequirementViewSet, basename='courserequirement')

urlpatterns = [
    path('', include(router.urls)),
]
