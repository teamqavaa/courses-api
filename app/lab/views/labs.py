from drf_spectacular.utils import extend_schema
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.sso import OptionalSSOAuthentication
from lab.models import Lab
from lab.serializers import LabSerializer

from .common import get_lab


@extend_schema(responses=LabSerializer(many=True))
@api_view(['GET'])
@authentication_classes([OptionalSSOAuthentication])
@permission_classes([AllowAny])
def lab_list(request):
    labs = (
        Lab.objects.filter(status=Lab.Status.PUBLISHED)
        .prefetch_related('objectives', 'skills')
        .order_by('title')
    )
    skill_slug = request.query_params.get('skill')
    if skill_slug:
        labs = labs.filter(skills__slug=skill_slug).distinct()

    return Response(LabSerializer(labs, many=True).data)


@extend_schema(responses=LabSerializer)
@api_view(['GET'])
@authentication_classes([OptionalSSOAuthentication])
@permission_classes([AllowAny])
def lab_detail(request, lab_ref):
    return Response(LabSerializer(get_lab(lab_ref)).data)
