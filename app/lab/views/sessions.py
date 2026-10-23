from datetime import timedelta

from django.db.models import F
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lab.models import LabSession, UserProgress
from lab.serializers import (
    OkSerializer,
    SessionGetResponseSerializer,
    SessionSaveRequestSerializer,
    SessionSaveResponseSerializer,
)

from .common import get_lab, get_user_id

ACTIVITY_GAP_CAP = timedelta(minutes=15)


def accumulate_practice_seconds(user_id, lab, previous_active_at, now):
    if previous_active_at is None:
        return
    delta = now - previous_active_at
    if delta <= timedelta(0) or delta > ACTIVITY_GAP_CAP:
        return
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return

    UserProgress.objects.get_or_create(
        user_id=user_id,
        lab=lab,
        defaults={'status': UserProgress.Status.IN_PROGRESS},
    )
    UserProgress.objects.filter(user_id=user_id, lab=lab).update(
        seconds_practiced=F('seconds_practiced') + seconds
    )


@extend_schema(methods=['GET'], responses=SessionGetResponseSerializer)
@extend_schema(
    methods=['POST'],
    request=SessionSaveRequestSerializer,
    responses=SessionSaveResponseSerializer,
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lab_session(request, lab_id):
    user_id = get_user_id(request)
    lab = get_lab(lab_id)

    if request.method == 'GET':
        session = LabSession.objects.filter(user_id=user_id, lab=lab).first()
        if session is None:
            return Response({
                'current_code': None,
                'status': 'not_started',
                'last_active_at': None,
            })
        return Response({
            'current_code': session.current_code,
            'status': session.status,
            'last_active_at': session.last_active_at,
        })

    payload = SessionSaveRequestSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    data = payload.validated_data
    completed_steps = data.get('completed_steps')
    now = timezone.now()

    previous = (
        LabSession.objects.filter(user_id=user_id, lab=lab)
        .only('last_active_at', 'status')
        .first()
    )
    previous_active = previous.last_active_at if previous else None

    defaults = {
        'current_code': data.get('current_code'),
        'last_active_at': now,
    }
    if previous is None or previous.status != LabSession.Status.COMPLETED:
        defaults['status'] = LabSession.Status.ACTIVE

    session, created = LabSession.objects.update_or_create(
        user_id=user_id,
        lab=lab,
        defaults=defaults,
    )

    if created:
        UserProgress.objects.update_or_create(
            user_id=user_id,
            lab=lab,
            defaults={
                'attempts': 1,
                'status': UserProgress.Status.IN_PROGRESS,
            },
        )
    else:
        progress = UserProgress.objects.filter(user_id=user_id, lab=lab).first()
        if progress is None:
            UserProgress.objects.create(
                user_id=user_id,
                lab=lab,
                status=UserProgress.Status.IN_PROGRESS,
            )
        elif progress.status != UserProgress.Status.COMPLETED:
            UserProgress.objects.filter(pk=progress.pk).update(
                status=UserProgress.Status.IN_PROGRESS
            )
        accumulate_practice_seconds(user_id, lab, previous_active, now)

    if completed_steps is not None:
        UserProgress.objects.filter(user_id=user_id, lab=lab).update(
            completed_steps=completed_steps
        )

    return Response({
        'id': session.id,
        'status': session.status,
        'last_active_at': session.last_active_at,
    })


@extend_schema(request=None, responses={200: OkSerializer, 404: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def heartbeat_session(request, lab_id):
    user_id = get_user_id(request)
    lab = get_lab(lab_id)
    now = timezone.now()
    session = LabSession.objects.filter(user_id=user_id, lab=lab).first()
    if session is None:
        return Response(
            {'error': 'No active session for this lab.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    accumulate_practice_seconds(user_id, lab, session.last_active_at, now)
    LabSession.objects.filter(pk=session.pk).update(last_active_at=now)
    return Response({'ok': True})


@extend_schema(request=None, responses=OkSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_session(request, lab_id):
    user_id = get_user_id(request)
    lab = get_lab(lab_id)
    now = timezone.now()

    previous = (
        LabSession.objects.filter(user_id=user_id, lab=lab)
        .only('last_active_at')
        .first()
    )
    LabSession.objects.update_or_create(
        user_id=user_id,
        lab=lab,
        defaults={
            'status': LabSession.Status.COMPLETED,
            'completed_at': now,
            'last_active_at': now,
        },
    )

    accumulate_practice_seconds(
        user_id,
        lab,
        previous.last_active_at if previous else None,
        now,
    )

    UserProgress.objects.update_or_create(
        user_id=user_id,
        lab=lab,
        defaults={
            'status': UserProgress.Status.COMPLETED,
            'completed_at': now,
        },
    )

    return Response({'ok': True})


@extend_schema(request=None, responses={200: OkSerializer, 404: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uncomplete_session(request, lab_id):
    user_id = get_user_id(request)
    lab = get_lab(lab_id)
    now = timezone.now()
    session = LabSession.objects.filter(user_id=user_id, lab=lab).first()
    if session is None:
        return Response(
            {'error': 'No session found for this lab.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    session.status = LabSession.Status.ACTIVE
    session.completed_at = None
    session.last_active_at = now
    session.save(update_fields=['status', 'completed_at', 'last_active_at'])

    UserProgress.objects.update_or_create(
        user_id=user_id,
        lab=lab,
        defaults={
            'status': UserProgress.Status.IN_PROGRESS,
            'completed_at': None,
        },
    )

    return Response({'ok': True})


@extend_schema(request=None, responses=OkSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_session(request, lab_id):
    user_id = get_user_id(request)
    lab = get_lab(lab_id)
    now = timezone.now()

    LabSession.objects.filter(user_id=user_id, lab=lab).update(
        current_code=None,
        status=LabSession.Status.ACTIVE,
        completed_at=None,
        last_active_at=now,
    )

    UserProgress.objects.filter(user_id=user_id, lab=lab).update(
        status=UserProgress.Status.IN_PROGRESS,
        attempts=0,
        completed_at=None,
        completed_steps=0,
    )

    return Response({'ok': True})


__all__ = [
    'complete_session',
    'heartbeat_session',
    'lab_session',
    'reset_session',
    'uncomplete_session',
]
