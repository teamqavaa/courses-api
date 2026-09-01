from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizAnswerViewSet

router = DefaultRouter()
router.register(r'quiz-answers', QuizAnswerViewSet, basename='quizanswer')

urlpatterns = [
    path('', include(router.urls)),
]
