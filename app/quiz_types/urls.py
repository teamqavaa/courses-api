from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TypeQuizViewSet

router = DefaultRouter()
router.register(r'quiz-types', TypeQuizViewSet, basename='quiztype')

urlpatterns = [
    path('', include(router.urls)),
]
