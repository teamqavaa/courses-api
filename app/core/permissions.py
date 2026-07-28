# app/courses/permissions.py
from rest_framework import permissions


class IsInstructorOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée basée sur l'utilisateur simulé (SimulatedUser).
    - Tout le monde (même anonyme) peut voir les cours (GET).
    - Seuls les administrateurs ou les instructeurs peuvent créer des cours (POST).
    - Un instructeur ne peut modifier ou supprimer (PUT/PATCH/DELETE) que ses propres cours.
    - Un administrateur peut tout modifier ou supprimer.
    """

    def has_permission(self, request, view):
        # 1. Permettre la lecture (GET, HEAD, OPTIONS) à tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2. Pour toute modification/création (POST, PUT, PATCH, DELETE) :
        # L'utilisateur doit être authentifié (X-User-Id présent dans les headers)
        if not (request.user and request.user.is_authenticated):
            return False

        # 3. L'utilisateur doit être soit admin, soit instructeur
        # On utilise ici directement les propriétés de votre classe SimulatedUser !
        return getattr(request.user, 'is_instructor', False) or getattr(request.user, 'is_admin', False)

    def has_object_permission(self, request, view, obj):
        """
        Contrôle d'accès au niveau d'un cours précis (ex: PUT/PATCH/DELETE sur /api/courses/<id>/)
        """
        # La lecture est toujours autorisée
        if request.method in permissions.SAFE_METHODS:
            return True

        # Un administrateur a tous les droits sur n'importe quel cours
        if getattr(request.user, 'is_admin', False):
            return True

        # Un instructeur ne peut modifier que ses propres cours.
        # On compare l'ID de l'utilisateur connecté avec l'instructor_id enregistré sur le cours.
        # (str() est utilisé par sécurité pour comparer proprement les chaînes d'UUID)
        return str(obj.instructor_id) == str(request.user.id)
