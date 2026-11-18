from django.urls import path

from . import views

urlpatterns = [
    path('quizzes/manage/', views.quiz_manage_list, name='quiz-manage-list'),
    path('quizzes/manage/<uuid:pk>/', views.quiz_manage_detail, name='quiz-manage-detail'),
    path('quizzes/<uuid:pk>/', views.quiz_detail, name='quiz-detail'),
    path('quizzes/<uuid:pk>/attempts/', views.start_attempt, name='quiz-start-attempt'),
    path('quiz-attempts/<uuid:pk>/', views.attempt_detail, name='quiz-attempt-detail'),
    path('quiz-attempts/<uuid:pk>/submit/', views.attempt_submit, name='quiz-attempt-submit'),
]
