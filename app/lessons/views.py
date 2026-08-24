# app/lessons/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from lessons.models import Lesson
from lessons.serializers import LessonDetailSerializer, LessonCreateUpdateSerializer


class HasSSORole(permissions.BasePermission):
    """
    Permission basée sur le rôle SSO transmis dans la requête (request.user).
    - Lecture (GET, HEAD, OPTIONS) : Ouverte à tout utilisateur authentifié.
    - Écriture (POST, PUT, PATCH, DELETE) : Réservée aux rôles 'instructor' ou 'admin'.
    """

    ALLOWED_WRITE_ROLES = {'instructor', 'admin', 'staff'}

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, 'role', None)
        return user_role in self.ALLOWED_WRITE_ROLES or getattr(request.user, 'is_staff', False)


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des Leçons (Lesson).

    - GET  /api/lessons/             : Liste des leçons (filtrable par module_id, lesson_type...)
    - GET  /api/lessons/{uuid}/      : Récupère le détail d'une leçon et sa vidéo liée
    - POST /api/lessons/             : Crée une leçon (Réservé rôle Instructor / Admin SSO)
    - PUT/PATCH /api/lessons/{uuid}/ : Modifie une leçon (Réservé rôle Instructor / Admin SSO)
    - DELETE /api/lessons/{uuid}/    : Supprime une leçon (Réservé rôle Instructor / Admin SSO)
    """

    permission_classes = [permissions.IsAuthenticated, HasSSORole]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['module', 'lesson_type', 'is_published', 'is_preview']

    def get_queryset(self):
        """
        Filtrage des leçons selon le rôle SSO :
        - Instructeurs / Admins : Voient toutes les leçons (publiées ou brouillons).
        - Autres rôles (ex: Étudiants) : Voient uniquement les leçons publiées.
        """
        user = self.request.user
        queryset = Lesson.objects.select_related('module').prefetch_related('video').all()

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
        - GET (liste, détail, by_module) : LessonDetailSerializer
        - POST/PUT/PATCH : LessonCreateUpdateSerializer
        """
        if self.action in ['list', 'retrieve', 'by_module']:
            return LessonDetailSerializer
        return LessonCreateUpdateSerializer

    @action(detail=False, methods=['get'], url_path='by-module/(?P<module_id>[^/.]+)')
    def by_module(self, request, module_id=None):
        """
        Endpoint utilitaire pour récupérer toutes les leçons d'un module spécifique dans l'ordre.
        - GET /api/lessons/by-module/{module_uuid}/
        """
        lessons = self.get_queryset().filter(module_id=module_id).order_by('order')
        serializer = LessonDetailSerializer(lessons, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
