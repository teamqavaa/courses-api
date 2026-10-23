from django.urls import path

from .views import (
    complete_session,
    execute_code,
    heartbeat_session,
    lab_detail,
    lab_list,
    lab_session,
    lab_stats,
    progress_detail,
    progress_list,
    reset_session,
    skill_detail,
    skill_labs,
    skill_list,
    uncomplete_session,
)

urlpatterns = [
    path('labs/', lab_list, name='lab-list'),
    path('labs/<str:lab_ref>/', lab_detail, name='lab-detail'),
    path('skills/', skill_list, name='skill-list'),
    path('skills/<slug:slug>/', skill_detail, name='skill-detail'),
    path('skills/<slug:slug>/labs/', skill_labs, name='skill-labs'),
    path('sessions/<uuid:lab_id>/', lab_session, name='lab-session'),
    path(
        'sessions/<uuid:lab_id>/heartbeat/',
        heartbeat_session,
        name='lab-session-heartbeat',
    ),
    path(
        'sessions/<uuid:lab_id>/complete/',
        complete_session,
        name='lab-session-complete',
    ),
    path(
        'sessions/<uuid:lab_id>/uncomplete/',
        uncomplete_session,
        name='lab-session-uncomplete',
    ),
    path(
        'sessions/<uuid:lab_id>/reset/',
        reset_session,
        name='lab-session-reset',
    ),
    path('execute/', execute_code, name='lab-execute'),
    path('progress/', progress_list, name='lab-progress-list'),
    path('progress/<uuid:lab_id>/', progress_detail, name='lab-progress-detail'),
    path('stats/', lab_stats, name='lab-stats'),
]
