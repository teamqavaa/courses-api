from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseLearningPointViewSet

router = DefaultRouter()
router.register(
    r'course-learning-points',
    CourseLearningPointViewSet,
    basename='course-learning-point'
)

urlpatterns = [
    path('', include(router.urls)),
]


