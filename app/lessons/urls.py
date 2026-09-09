from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LessonViewSet, LabActivityViewSet

router = DefaultRouter()
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'lab-activities', LabActivityViewSet, basename='lab-activity')

urlpatterns = [
    path('', include(router.urls)),
]
