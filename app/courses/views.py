from django.db.models import Case, IntegerField, ProtectedError, Q, Value, When
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
from .serializers import CourseManageSerializer, CourseSearchSerializer, CourseSerializer, CourseStatusSerializer
from core.utils import get_user_sub_from_request

# Statuts qu'un instructeur peut donner à son propre cours (la publication est réservée aux admins)
INSTRUCTOR_STATUSES = {'draft', 'review'}

SEARCH_MIN_LENGTH = 2
SEARCH_DEFAULT_LIMIT = 20
SEARCH_MAX_LIMIT = 50


def _search_filter(term):
    """Un mot de la recherche : présent dans au moins un des champs publics du cours."""
    return (
        Q(title__icontains=term)
        | Q(subtitle__icontains=term)
        | Q(description__icontains=term)
        | Q(instructor_name__icontains=term)
        | Q(category__name__icontains=term)
        | Q(tags__name__icontains=term)
        | Q(modules__title__icontains=term, modules__is_published=True)
        | Q(modules__lessons__title__icontains=term, modules__lessons__is_published=True)
    )


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
        extra = {}
        user = self.request.user
        # Cours créés avant le champ instructor_name : complété quand le propriétaire le modifie
        if not serializer.instance.instructor_name and serializer.instance.user_id == str(user.id):
            extra['instructor_name'] = getattr(user, 'name', '') or ''
        serializer.save(**extra)

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

    @extend_schema(
        parameters=[
            OpenApiParameter('q', str, description="Mots recherchés (au moins 2 caractères)"),
            OpenApiParameter('limit', int, description=f"Nombre de résultats (max {SEARCH_MAX_LIMIT})"),
        ],
        responses=CourseSearchSerializer(many=True),
    )
    @action(detail=False, methods=['get'], url_path='search', permission_classes=[])
    def search(self, request):
        """
        GET /api/courses/search/?q=figma&limit=20 — recherche publique dans les cours publiés.
        Chaque mot doit apparaître dans le titre, le sous-titre, la description, le formateur,
        la catégorie, un tag, un module ou une leçon. Les correspondances dans le titre d'abord.
        Réponse : {"query", "count", "results": [...]}.
        """
        query = ' '.join(request.query_params.get('q', '').split())
        try:
            limit = min(max(int(request.query_params.get('limit', SEARCH_DEFAULT_LIMIT)), 1), SEARCH_MAX_LIMIT)
        except ValueError:
            limit = SEARCH_DEFAULT_LIMIT
        if len(query) < SEARCH_MIN_LENGTH:
            return Response({'query': query, 'count': 0, 'results': []})

        terms = query.split()[:8]
        matching = Course.objects.filter(status='published')
        for term in terms:
            matching = matching.filter(_search_filter(term))

        title_match = Q()
        for term in terms:
            title_match &= Q(title__icontains=term)
        courses = (
            Course.objects.filter(pk__in=matching.values('pk'))
            .select_related('category')
            .prefetch_related('modules__lessons')
            .annotate(rank=Case(When(title_match, then=Value(0)), default=Value(1), output_field=IntegerField()))
            .order_by('rank', '-total_students', 'title')
        )
        count = courses.count()
        return Response({
            'query': query,
            'count': count,
            'results': CourseSearchSerializer(courses[:limit], many=True).data,
        })

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
