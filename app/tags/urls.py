# app/tags/urls.py (ou app/courses/urls_tags.py selon votre structure)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tags.views import TagViewSet

router = DefaultRouter()
# CORRECTION : On nomme explicitement le préfixe 'tags' au lieu de ''
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
