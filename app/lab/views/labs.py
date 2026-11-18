from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.permissions import can_edit_lab, ensure_can_edit_lab, ensure_can_manage_labs
from core.sso import OptionalSSOAuthentication
from lab.models import Lab, LabSession
from lab.serializers import (
    LabManageSerializer,
    LabSerializer,
    LabStatusSerializer,
    LabWriteSerializer,
)

from .common import get_lab, visible_labs

# Statuts qu'un instructeur peut donner à son lab ; seul un admin publie.
INSTRUCTOR_STATUSES = {Lab.Status.DRAFT, Lab.Status.REVIEW}


def _check_status_allowed(user, new_status):
    if new_status and new_status not in INSTRUCTOR_STATUSES and not user.is_admin:
        raise PermissionDenied("Seul un administrateur peut publier un lab.")


def _manage_data(lab):
    """Lab relu avec ses étapes et compétences à jour (après création / modification)."""
    lab = Lab.objects.prefetch_related('objectives', 'skills').get(pk=lab.pk)
    return LabManageSerializer(lab).data


@extend_schema(
    methods=['GET'],
    parameters=[OpenApiParameter('skill', str, description="Slug d'une compétence")],
    responses=LabSerializer(many=True),
)
@extend_schema(methods=['POST'], request=LabWriteSerializer, responses=LabManageSerializer)
@api_view(['GET', 'POST'])
@authentication_classes([OptionalSSOAuthentication])
@permission_classes([AllowAny])
def lab_list(request):
    """
    GET : labs publiés ; un instructeur voit aussi les siens, un admin tous les labs.
    POST : création (instructeur ou admin) ; le lab appartient au `sub` du token.
    """
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentification requise.'}, status=status.HTTP_401_UNAUTHORIZED)
        ensure_can_manage_labs(request.user)
        serializer = LabWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _check_status_allowed(request.user, serializer.validated_data.get('status'))
        lab = serializer.save(
            user_id=str(request.user.id),
            user_email=getattr(request.user, 'email', '') or '',
            author_name=getattr(request.user, 'name', '') or '',
        )
        return Response(_manage_data(lab), status=status.HTTP_201_CREATED)

    labs = visible_labs(request.user).order_by('title')
    skill_slug = request.query_params.get('skill')
    if skill_slug:
        labs = labs.filter(skills__slug=skill_slug).distinct()
    return Response(LabSerializer(labs, many=True).data)


@extend_schema(methods=['GET'], responses=LabSerializer)
@extend_schema(methods=['PATCH'], request=LabWriteSerializer, responses=LabManageSerializer)
@extend_schema(methods=['DELETE'], responses={204: None, 409: None})
@api_view(['GET', 'PATCH', 'DELETE'])
@authentication_classes([OptionalSSOAuthentication])
@permission_classes([AllowAny])
def lab_detail(request, lab_ref):
    """
    GET : lab visible par l'utilisateur (brouillon : auteur et admins seulement).
    PATCH / DELETE : admin, ou instructeur auteur du lab.
    """
    lab = get_lab(lab_ref, request.user)
    if request.method == 'GET':
        # L'email de l'auteur n'est renvoyé qu'à l'auteur et aux admins
        serializer = LabManageSerializer if can_edit_lab(request.user, lab) else LabSerializer
        return Response(serializer(lab).data)

    if not request.user.is_authenticated:
        return Response({'detail': 'Authentification requise.'}, status=status.HTTP_401_UNAUTHORIZED)
    ensure_can_edit_lab(request.user, lab)

    if request.method == 'DELETE':
        # Un instructeur ne supprime pas un lab déjà commencé par des apprenants : il le repasse en brouillon
        started = LabSession.objects.filter(lab=lab).exclude(user_id=str(request.user.id)).exists()
        if started and not request.user.is_admin:
            return Response(
                {'detail': "Des apprenants ont commencé ce lab : il ne peut pas être supprimé. "
                           "Passez-le en brouillon pour le retirer du catalogue."},
                status=status.HTTP_409_CONFLICT,
            )
        # Lab utilisé par une leçon de cours (Lesson.lab, on_delete=PROTECT) : 409 plutôt qu'une 500
        if lab.lessons.exists():
            return Response(
                {'detail': "Ce lab est utilisé par une leçon de cours : retirez-le du programme avant de le supprimer."},
                status=status.HTTP_409_CONFLICT,
            )
        lab.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = LabWriteSerializer(lab, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    _check_status_allowed(request.user, serializer.validated_data.get('status'))
    extra = {}
    # Labs créés avant le champ author_name : complété quand l'auteur le modifie
    if not lab.author_name and lab.user_id == str(request.user.id):
        extra['author_name'] = getattr(request.user, 'name', '') or ''
    lab = serializer.save(**extra)
    return Response(_manage_data(lab))


@extend_schema(request=LabStatusSerializer, responses=LabManageSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lab_status(request, lab_ref):
    """
    POST /api/labs/<ref>/status/ {"status": "draft" | "review" | "published"}
    Instructeur auteur : draft <-> review. Admin : tous les statuts.
    """
    lab = get_lab(lab_ref, request.user)
    ensure_can_edit_lab(request.user, lab)
    serializer = LabStatusSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    _check_status_allowed(request.user, serializer.validated_data['status'])
    lab.status = serializer.validated_data['status']
    lab.save(update_fields=['status', 'updated_at'])
    return Response(_manage_data(lab))


@extend_schema(
    parameters=[
        OpenApiParameter('status', str, enum=['draft', 'review', 'published']),
        OpenApiParameter('search', str, description='Recherche dans le titre et le slug'),
    ],
    responses=LabManageSerializer(many=True),
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lab_manage(request):
    """
    GET /api/labs/manage/ — labs gérables : tous pour un admin, les siens pour un instructeur
    (403 pour un étudiant).
    """
    ensure_can_manage_labs(request.user)
    labs = Lab.objects.prefetch_related('objectives', 'skills')
    if not request.user.is_admin:
        labs = labs.filter(user_id=str(request.user.id))
    if request.query_params.get('status'):
        labs = labs.filter(status=request.query_params['status'])
    search = request.query_params.get('search', '').strip()
    if search:
        labs = labs.filter(Q(title__icontains=search) | Q(slug__icontains=search))
    return Response(LabManageSerializer(labs.order_by('-updated_at'), many=True).data)
