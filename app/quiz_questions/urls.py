from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionViewSet

router = DefaultRouter()
router.register(r'quiz-questions', QuestionViewSet, basename='quizquestion')

urlpatterns = [
    path('', include(router.urls)),
]
