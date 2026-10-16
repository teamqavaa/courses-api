from django.db.models import ProtectedError, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import CanManageCourses, ensure_can_edit_course
from core.sso import OptionalSSOAuthentication
from courses.models import Course
from enrollments.models import Enrollment
from .serializers import CourseManageSerializer, CourseSerializer, CourseStatusSerializer
from core.utils import get_user_sub_from_request

# Statuts qu'un instructeur peut donner à son propre cours (la publication est réservée aux admins)
INSTRUCTOR_STATUSES = {'draft', 'review'}


class CourseViewSet(viewsets.ModelViewSet):
    """
    Catalogue et gestion des cours.

    - Lecture (liste, détail) : publique, uniquement les cours publiés. Un instructeur voit aussi
      ses propres cours, un administrateur voit tout.
    - Création : instructeur ou administrateur (le cours appartient au `sub` du token).
    - Modification / suppression : administrateur, ou instructeur propriétaire.
    - Statut : un instructeur passe son cours de `draft` à `review` (soumission) ;
      seul un administrateur publie (`published`) ou remet en brouillon.
    """
    serializer_class = CourseSerializer
    lookup_field = 'slug'
    # Un token expiré ne doit pas bloquer la lecture du catalogue
    authentication_classes = [OptionalSSOAuthentication]
    permission_classes = [CanManageCourses]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = Course.objects.all().select_related('category').prefetch_related(
            'tags',
            'highlights',
            'learning_points',
            'outcomes',
            'modules__lessons__video',
            'modules__lessons__resources',
            'modules__resources',
            'resources'
        )
        if self.action in ('list', 'retrieve'):
            return self._visible(queryset)
        return queryset

    def _visible(self, queryset):
        user = self.request.user
        if getattr(user, 'is_admin', False):
            return queryset
        if getattr(user, 'is_instructor', False):
            return queryset.filter(Q(status='published') | Q(user_id=str(user.id)))
        return queryset.filter(status='published')

    def _check_status_allowed(self, new_status):
        if new_status and new_status not in INSTRUCTOR_STATUSES and not self.request.user.is_admin:
            raise PermissionDenied("Seul un administrateur peut publier un cours.")

    def perform_create(self, serializer):
        self._check_status_allowed(serializer.validated_data.get('status'))
        serializer.save()

    def perform_update(self, serializer):
        self._check_status_allowed(serializer.validated_data.get('status'))
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        course = self.get_object()
        try:
            course.delete()
        except ProtectedError:
            return Response(
                {"detail": "Ce cours a déjà été commandé : il ne peut pas être supprimé. "
                           "Passez-le en brouillon pour le retirer du catalogue."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        parameters=[
            OpenApiParameter('status', str, enum=['draft', 'review', 'published']),
            OpenApiParameter('search', str, description="Recherche dans le titre"),
        ],
        responses=CourseManageSerializer(many=True),
    )
    @action(detail=False, methods=['get'], url_path='manage', permission_classes=[IsAuthenticated])
    def manage(self, request):
        """
        GET /api/courses/manage/ — cours gérables par l'utilisateur :
        tous pour un administrateur, les siens pour un instructeur.
        """
        user = request.user
        if not user.is_instructor:
            raise PermissionDenied("Réservé aux instructeurs et aux administrateurs.")

        queryset = Course.objects.select_related('category').prefetch_related('modules__lessons')
        if not user.is_admin:
            queryset = queryset.filter(user_id=str(user.id))
        if request.query_params.get('status'):
            queryset = queryset.filter(status=request.query_params['status'])
        if request.query_params.get('search'):
            queryset = queryset.filter(title__icontains=request.query_params['search'])

        return Response(CourseManageSerializer(queryset.order_by('-updated_at'), many=True).data)

    @extend_schema(request=CourseStatusSerializer, responses=CourseManageSerializer)
    @action(detail=True, methods=['post'], url_path='status')
    def set_status(self, request, slug=None):
        """
        POST /api/courses/<slug>/status/ {"status": "draft" | "review" | "published"}
        Instructeur propriétaire : draft <-> review. Administrateur : tous les statuts.
        """
        course = self.get_object()
        ensure_can_edit_course(request.user, course)
        serializer = CourseStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._check_status_allowed(serializer.validated_data['status'])

        course.status = serializer.validated_data['status']
        course.save(update_fields=['status', 'updated_at'])
        return Response(CourseManageSerializer(course).data)

    @action(detail=False, methods=['get'], url_path='my-enrollments')
    def my_enrollments(self, request):
        """
        GET /api/courses/my-enrollments/
        """
        try:
            current_user_id = get_user_sub_from_request(request)
        except AuthenticationFailed as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        # Récupère les IDs des cours liés aux inscriptions de l'utilisateur
        enrolled_course_ids = Enrollment.objects.filter(user_id=current_user_id).values_list('course_id', flat=True)
        courses = self.get_queryset().filter(id__in=enrolled_course_ids)

        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
