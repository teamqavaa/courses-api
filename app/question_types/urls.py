from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TypeQuestionViewSet

router = DefaultRouter()
router.register(r'question-types', TypeQuestionViewSet, basename='questiontype')

urlpatterns = [
    path('', include(router.urls)),
]
