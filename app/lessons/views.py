# app/lessons/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import CanManageCourses, course_of, ensure_can_edit_course
from lessons.models import Lesson
from lessons.serializers import LessonDetailSerializer, LessonCreateUpdateSerializer


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des Leçons (Lesson).

    - GET  /api/lessons/             : Liste des leçons (filtrable par module_id, lesson_type...)
    - GET  /api/lessons/{uuid}/      : Récupère le détail d'une leçon et sa vidéo liée
    - POST /api/lessons/             : Crée une leçon (Réservé rôle Instructor / Admin SSO)
    - PUT/PATCH /api/lessons/{uuid}/ : Modifie une leçon (Réservé rôle Instructor / Admin SSO)
    - DELETE /api/lessons/{uuid}/    : Supprime une leçon (Réservé rôle Instructor / Admin SSO)
    """

    permission_classes = [permissions.IsAuthenticated, CanManageCourses]
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

        if getattr(user, 'is_instructor', False):
            return queryset

        return queryset.filter(is_published=True)

    def perform_create(self, serializer):
        # Un instructeur n'ajoute du contenu qu'à ses propres cours
        ensure_can_edit_course(self.request.user, course_of(serializer.validated_data.get('module')))
        serializer.save()

    def perform_update(self, serializer):
        if serializer.validated_data.get('module'):
            ensure_can_edit_course(self.request.user, course_of(serializer.validated_data.get('module')))
        serializer.save()

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
