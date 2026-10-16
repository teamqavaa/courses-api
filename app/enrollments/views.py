from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.sso import SSOAuthentication
from .models import Enrollment
from .serializers import (
    DashboardEnrollmentSerializer,
    LessonProgressInputSerializer,
    LessonProgressSerializer,
)
from .services import course_lessons, learning_stats, record_lesson_progress


class EnrollmentViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    Inscriptions de l'utilisateur connecté (sub du token SSO) et progression de lecture.

    - GET  /api/enrollments/                 : cours inscrits, triés par dernier accès
    - GET  /api/enrollments/<slug>/          : inscription à un cours (slug du cours)
    - POST /api/enrollments/<slug>/progress/ : position de lecture / leçon terminée
    - GET  /api/enrollments/stats/?days=7    : statistiques du dashboard
    """
    serializer_class = DashboardEnrollmentSerializer
    authentication_classes = [SSOAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'course__slug'
    lookup_url_kwarg = 'slug'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        return (
            Enrollment.objects.filter(user_id=str(self.request.user.id))
            .exclude(status='suspended')
            .select_related('course__category')
            .prefetch_related('lesson_progress__lesson')
            .order_by('-last_accessed_at')
        )

    @extend_schema(request=LessonProgressInputSerializer, responses=DashboardEnrollmentSerializer)
    @action(detail=True, methods=['post'], url_path='progress')
    def progress(self, request, slug=None):
        enrollment = self.get_object()
        data = LessonProgressInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        lesson = course_lessons(enrollment.course).filter(id=data.validated_data['lesson_id']).first()
        if lesson is None:
            return Response(
                {'detail': "Cette leçon n'appartient pas à ce cours."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        progress = record_lesson_progress(
            enrollment,
            lesson,
            position_seconds=data.validated_data.get('position_seconds'),
            completed=data.validated_data['completed'],
        )
        enrollment = self.get_queryset().get(pk=enrollment.pk)
        return Response({
            'lesson_progress': LessonProgressSerializer(progress).data,
            'enrollment': DashboardEnrollmentSerializer(enrollment).data,
        })

    @extend_schema(parameters=[OpenApiParameter('days', int, description="Nombre de jours (1-90, défaut 7)")])
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        try:
            days = min(max(int(request.query_params.get('days', 7)), 1), 90)
        except ValueError:
            days = 7
        return Response(learning_stats(str(request.user.id), days=days))
