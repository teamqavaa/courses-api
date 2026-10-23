from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lab.models import LabObjective, UserProgress
from lab.serializers import ProgressSerializer

from .common import get_user_id


def _serialize(progress):
    total_steps = LabObjective.objects.filter(lab=progress.lab).count()
    if progress.status == UserProgress.Status.COMPLETED:
        progress_percent = 100
    elif total_steps == 0:
        progress_percent = 0
    else:
        progress_percent = round(progress.completed_steps / total_steps * 100)

    return {
        'lab_id': progress.lab_id,
        'status': progress.status,
        'attempts': progress.attempts,
        'completed_at': progress.completed_at,
        'completed_steps': progress.completed_steps,
        'total_steps': total_steps,
        'progress_percent': progress_percent,
    }


@extend_schema(responses=ProgressSerializer(many=True))
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progress_list(request):
    user_id = get_user_id(request)
    records = UserProgress.objects.filter(user_id=user_id).select_related('lab')
    return Response([_serialize(record) for record in records])


@extend_schema(responses=ProgressSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progress_detail(request, lab_id):
    user_id = get_user_id(request)
    progress = (
        UserProgress.objects.filter(user_id=user_id, lab_id=lab_id)
        .select_related('lab')
        .first()
    )
    if progress is None:
        return Response({
            'status': 'not_started',
            'attempts': 0,
            'completed_steps': 0,
            'total_steps': LabObjective.objects.filter(lab_id=lab_id).count(),
            'progress_percent': 0,
        })
    return Response(_serialize(progress))
