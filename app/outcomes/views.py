# app/courses/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from outcomes.models import CourseOutcome
from outcomes.serializers import (
    CourseOutcomeDetailSerializer,
    CourseOutcomeCreateUpdateSerializer
)


class HasSSORole(permissions.BasePermission):
    """
    Permission basée sur le rôle SSO transmis dans la requête (request.user).
    - Lecture : Ouverte à tout utilisateur (ou anonymes pour les landing pages).
    - Écriture : Réservée aux rôles 'instructor', 'admin' ou 'staff'.
    """
    ALLOWED_WRITE_ROLES = {'instructor', 'admin', 'staff'}

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, 'role', None)
        return user_role in self.ALLOWED_WRITE_ROLES or getattr(request.user, 'is_staff', False)


class CourseOutcomeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des Objectifs / Acquis de Cours (CourseOutcome).

    - GET    /api/course-outcomes/             : Liste des objectifs (filtrable par course)
    - GET    /api/course-outcomes/{uuid}/      : Récupère un objectif spécifique
    - POST   /api/course-outcomes/             : Crée un objectif (Instructor / Admin SSO)
    - PUT/PATCH /api/course-outcomes/{uuid}/   : Modifie un objectif (Instructor / Admin SSO)
    - DELETE /api/course-outcomes/{uuid}/      : Supprime un objectif (Instructor / Admin SSO)
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, HasSSORole]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'category', 'is_highlighted', 'is_published']

    def get_queryset(self):
        """
        Filtrage des objectifs :
        - Instructeurs / Admins : Voient tous les objectifs (publiés ou non).
        - Autres utilisateurs : Voient uniquement les objectifs masqués/publiés selon `is_published`.
        """
        user = self.request.user
        queryset = CourseOutcome.objects.select_related('course').all()

        if user.is_authenticated:
            user_role = getattr(user, 'role', None)
            is_admin_or_instructor = (
                user_role in {'instructor', 'admin', 'staff'} or
                getattr(user, 'is_staff', False)
            )
            if is_admin_or_instructor:
                return queryset

        return queryset.filter(is_published=True)

    def get_serializer_class(self):
        """
        Bascule de serializer selon l'action :
        - GET (list, retrieve, by_course) : CourseOutcomeDetailSerializer
        - POST / PUT / PATCH : CourseOutcomeCreateUpdateSerializer
        """
        if self.action in ['list', 'retrieve', 'by_course']:
            return CourseOutcomeDetailSerializer
        return CourseOutcomeCreateUpdateSerializer

    @action(detail=False, methods=['get'], url_path='by-course/(?P<course_id>[^/.]+)')
    def by_course(self, request, course_id=None):
        """
        Endpoint utilitaire pour récupérer les objectifs d'un cours spécifique dans l'ordre.
        - GET /api/course-outcomes/by-course/{course_uuid}/
        """
        outcomes = self.get_queryset().filter(course_id=course_id).order_by('order')
        serializer = CourseOutcomeDetailSerializer(outcomes, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

