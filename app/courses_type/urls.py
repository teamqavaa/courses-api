# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TypeCourseViewSet

router = DefaultRouter()
router.register(r'course-types', TypeCourseViewSet, basename='coursetype')

urlpatterns = [
    path('', include(router.urls)),
]
