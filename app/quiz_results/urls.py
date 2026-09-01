from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResultViewSet

router = DefaultRouter()
router.register(r'quiz-results', ResultViewSet, basename='quizresult')

urlpatterns = [
    path('', include(router.urls)),
]
