from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lab.models import LabSession, UserProgress
from lab.serializers import StatsSerializer

from .common import get_user_id

WEEK_START_MONDAY = 0


@extend_schema(responses=StatsSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lab_stats(request):
    user_id = get_user_id(request)

    labs_completed = UserProgress.objects.filter(
        user_id=user_id,
        status=UserProgress.Status.COMPLETED,
    ).count()

    total_seconds = (
        UserProgress.objects.filter(user_id=user_id).aggregate(
            total=Sum('seconds_practiced')
        )['total']
        or 0
    )
    hours_practiced = round(total_seconds / 3600, 1)

    today = timezone.now().date()
    active_dates = (
        LabSession.objects.filter(user_id=user_id, last_active_at__isnull=False)
        .values_list('last_active_at', flat=True)
        .distinct()
    )
    active_date_set = {value.date() for value in active_dates}

    check_date = today if today in active_date_set else today - timedelta(days=1)
    streak = 0
    while check_date in active_date_set:
        streak += 1
        check_date -= timedelta(days=1)

    week_start = today - timedelta(days=(today.weekday() - WEEK_START_MONDAY) % 7)
    week = [
        {
            'date': (week_start + timedelta(days=offset)).isoformat(),
            'practiced': (week_start + timedelta(days=offset)) in active_date_set,
            'is_today': (week_start + timedelta(days=offset)) == today,
        }
        for offset in range(7)
    ]

    return Response({
        'labs_completed': labs_completed,
        'hours_practiced': hours_practiced,
        'current_streak': streak,
        'week': week,
    })
