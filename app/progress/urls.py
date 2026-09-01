# urls.py
from django.urls import path

from .views import (
    CompleteCourseView,
    MyCourseStatsView,
    MyProgressView,
    RecommendationView,
    SingleMyProgressView,
    StartCourseView,
    UncompleteCourseView,
)

urlpatterns = [
    path('my/recommendation/', RecommendationView.as_view()),
    path('my/course-stats/', MyCourseStatsView.as_view()),
    path('my/progress/', MyProgressView.as_view()),
    path('my/progress/<str:course_id>/', SingleMyProgressView.as_view()),
    path('my/progress/<str:course_id>/start/', StartCourseView.as_view()),
    path('my/progress/<str:course_id>/complete/', CompleteCourseView.as_view()),
    path('my/progress/<str:course_id>/uncomplete/', UncompleteCourseView.as_view()),
]