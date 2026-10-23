from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.sso import OptionalSSOAuthentication
from lab.models import Lab, Skill
from lab.serializers import LabSerializer, SkillDetailSerializer, SkillSerializer


@extend_schema(responses=SkillSerializer(many=True))
@api_view(['GET'])
@authentication_classes([OptionalSSOAuthentication])
@permission_classes([AllowAny])
def skill_list(request):
    skills = Skill.objects.filter(is_active=True).annotate(
        lab_count=Count('labs', distinct=True)
    )
    return Response(SkillSerializer(skills, many=True).data)


@extend_schema(responses=SkillDetailSerializer)
@api_view(['GET'])
@authentication_classes([OptionalSSOAuthentication])
@permission_classes([AllowAny])
def skill_detail(request, slug):
    try:
        skill = Skill.objects.prefetch_related(
            'outcomes',
            'prerequisites',
            'labs',
        ).get(slug=slug, is_active=True)
    except Skill.DoesNotExist:
        raise Http404('Compétence introuvable.')
    return Response(SkillDetailSerializer(skill).data)


@extend_schema(responses=LabSerializer(many=True))
@api_view(['GET'])
@authentication_classes([OptionalSSOAuthentication])
@permission_classes([AllowAny])
def skill_labs(request, slug):
    skill = get_object_or_404(Skill, slug=slug, is_active=True)
    labs = (
        Lab.objects.filter(status=Lab.Status.PUBLISHED, skills=skill)
        .prefetch_related('objectives', 'skills')
        .order_by('title')
    )
    return Response(LabSerializer(labs, many=True).data)
