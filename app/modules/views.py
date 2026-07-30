from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from modules.models import Module
from modules.serializers import ModuleDetailSerializer, ModuleCreateUpdateSerializer  # 👈 Nom corrigé ici


class HasSSORole(permissions.BasePermission):
    """
    Permission basée sur le rôle SSO transmis dans la requête (request.user).
    - Lecture (GET, HEAD, OPTIONS) : Ouverte à tous les utilisateurs authentifiés.
    - Écriture (POST, PUT, PATCH, DELETE) : Réservée aux rôles 'instructor' ou 'admin'.
    """

    ALLOWED_WRITE_ROLES = {'instructor', 'admin', 'staff'}

    def has_permission(self, request, view):
        # Pour les méthodes de lecture, on autorise tout utilisateur authentifié
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        # On extrait le rôle rattaché à l'utilisateur (issu du Token SSO / Claim JWT)
        user_role = getattr(request.user, 'role', None)

        # Vérification si le rôle correspond ou si l'attribut Django standard is_staff est vrai
        if user_role in self.ALLOWED_WRITE_ROLES or getattr(request.user, 'is_staff', False):
            return True

        return False


class ModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des Modules via Authentification SSO.

    - GET  /api/modules/             : Liste des modules (filtrable par course)
    - GET  /api/modules/{uuid}/      : Récupère uniquement les infos du module
    - POST /api/modules/             : Crée un module (Réservé rôle Instructor / Admin SSO)
    - PUT/PATCH /api/modules/{uuid}/ : Modifie un module (Réservé rôle Instructor / Admin SSO)
    - DELETE /api/modules/{uuid}/    : Supprime un module (Réservé rôle Instructor / Admin SSO)
    """
    permission_classes = [permissions.IsAuthenticated, HasSSORole]
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
