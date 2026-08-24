# app/highlights/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseHighlightViewSet

router = DefaultRouter()
router.register(r'course-highlights', CourseHighlightViewSet, basename='course-highlight')

urlpatterns = [
    path('', include(router.urls)),
]
