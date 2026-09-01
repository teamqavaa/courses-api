from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizOptionViewSet

router = DefaultRouter()
router.register(r'quiz-options', QuizOptionViewSet, basename='quizoption')

urlpatterns = [
    path('', include(router.urls)),
]
