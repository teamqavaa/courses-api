# app/videos/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import CanManageCourses, course_of, ensure_can_edit_course

from .models import Video
from .serializers import VideoSerializer, VideoReadPublicSerializer


class VideoViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des Vidéos de leçons.

    - GET    /api/videos/             : Liste des vidéos (filtrable par lesson, provider)
    - GET    /api/videos/{uuid}/      : Métadonnées et flux d'une vidéo
    - POST   /api/videos/             : Rattache une vidéo à une leçon (Instructor / Admin SSO)
    - PUT/PATCH /api/videos/{uuid}/   : Modifie les paramètres de la vidéo (Instructor / Admin SSO)
    - DELETE /api/videos/{uuid}/      : Supprime une vidéo (Instructor / Admin SSO)
    """

    permission_classes = [permissions.IsAuthenticated, CanManageCourses]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['lesson', 'provider']

    def get_queryset(self):
        return Video.objects.select_related('lesson').all()

    def perform_create(self, serializer):
        # Un instructeur n'ajoute du contenu qu'à ses propres cours
        ensure_can_edit_course(self.request.user, course_of(serializer.validated_data.get('lesson')))
        serializer.save()

    def perform_update(self, serializer):
        if serializer.validated_data.get('lesson'):
            ensure_can_edit_course(self.request.user, course_of(serializer.validated_data.get('lesson')))
        serializer.save()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'by_lesson']:
            return VideoReadPublicSerializer
        return VideoSerializer

    @action(detail=False, methods=['get'], url_path='by-lesson/(?P<lesson_id>[^/.]+)')
    def by_lesson(self, request, lesson_id=None):
        """
        Endpoint utilitaire pour récupérer la vidéo d'une leçon spécifique.
        - GET /api/videos/by-lesson/{lesson_uuid}/
        """
        try:
            video = self.get_queryset().get(lesson_id=lesson_id)
            serializer = VideoReadPublicSerializer(video, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Video.DoesNotExist:
            return Response(
                {"detail": "Aucune vidéo associée à cette leçon."},
                status=status.HTTP_404_NOT_FOUND
            )

