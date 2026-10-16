from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import CanManageCourses, course_of, ensure_can_edit_course

from modules.models import Module
from modules.serializers import ModuleDetailSerializer, ModuleCreateUpdateSerializer  # 👈 Nom corrigé ici


class ModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des Modules via Authentification SSO.

    - GET  /api/modules/             : Liste des modules (filtrable par course)
    - GET  /api/modules/{uuid}/      : Récupère uniquement les infos du module
    - POST /api/modules/             : Crée un module (Réservé rôle Instructor / Admin SSO)
    - PUT/PATCH /api/modules/{uuid}/ : Modifie un module (Réservé rôle Instructor / Admin SSO)
    - DELETE /api/modules/{uuid}/    : Supprime un module (Réservé rôle Instructor / Admin SSO)
    """
    permission_classes = [permissions.IsAuthenticated, CanManageCourses]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'is_published', 'is_free']

    def get_queryset(self):
        """
        Filtrage des modules selon le rôle SSO :
        - Instructeurs / Admins : Voient tous les modules (publiés ou brouillons).
        - Autres rôles (ex: Étudiants) : Voient uniquement les modules publiés.
        """
        user = self.request.user
        queryset = Module.objects.select_related('course').all()

        if getattr(user, 'is_instructor', False):
            return queryset

        return queryset.filter(is_published=True)

    def perform_create(self, serializer):
        # Un instructeur n'ajoute du contenu qu'à ses propres cours
        ensure_can_edit_course(self.request.user, course_of(serializer.validated_data.get('course')))
        serializer.save()

    def perform_update(self, serializer):
        if serializer.validated_data.get('course'):
            ensure_can_edit_course(self.request.user, course_of(serializer.validated_data.get('course')))
        serializer.save()

    def get_serializer_class(self):
        """
        - GET : Retourne uniquement les infos du module via ModuleDetailSerializer.
        - POST/PUT/PATCH : Utilise ModuleCreateUpdateSerializer.
        """
        if self.action in ['list', 'retrieve', 'by_course']:
            return ModuleDetailSerializer
        return ModuleCreateUpdateSerializer  # 👈 Nom corrigé ici

    @action(detail=False, methods=['get'], url_path='by-course/(?P<course_id>[^/.]+)')
    def by_course(self, request, course_id=None):
        """
        Endpoint utilitaire pour récupérer les modules d'un cours spécifique.
        - GET /api/modules/by-course/{course_uuid}/
        """
        modules = self.get_queryset().filter(course_id=course_id).order_by('order')
        serializer = ModuleDetailSerializer(modules, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
