import os

import requests
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class IsInstructorOrAdmin(permissions.BasePermission):
    """
    Permission basée sur l'utilisateur simulé (SimulatedUser / ClaimUser).
    - Tout le monde (même anonyme) peut voir les cours (GET).
    - Seuls les administrateurs ou les instructeurs peuvent créer (POST) ou
      modifier / supprimer (PUT/PATCH/DELETE).
    - Un instructeur ne peut modifier ou supprimer que ses propres cours.
    """

    # Rôles autorisés pour l'écriture.
    ALLOWED_WRITE_ROLES = {'instructor', 'admin', 'staff'}

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        if getattr(request.user, 'is_instructor', False) or getattr(request.user, 'is_admin', False):
            return True
        if getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False):
            return True
        return getattr(request.user, 'role', None) in self.ALLOWED_WRITE_ROLES

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if getattr(request.user, 'is_admin', False):
            return True
        if getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False):
            return True
        if getattr(request.user, 'role', None) == 'admin':
            return True

        # Un instructeur ne peut modifier que ses propres cours
        # (str() compare proprement les UUID, y compris contre un claim `sub`).
        return str(obj.instructor_id) == str(request.user.id)


class SimulatedUser:
    """Objet utilisateur minimaliste pour satisfaire DRF lors de l'introspection."""

    def __init__(self, user_data):
        self.id = user_data.get('sub') or user_data.get('user_id')
        self.pk = self.id
        self.email = user_data.get('email') or ''
        self.roles = user_data.get('roles') or []
        self.is_authenticated = True
        self.is_active = True
        # Compat: explicit boolean claims (is_instructor / is_admin) take
        # precedence; otherwise they are derived from the `roles` list.
        self.is_instructor = user_data.get(
            'is_instructor',
            'admin' in self.roles or 'instructor' in self.roles,
        )
        self.is_admin = user_data.get(
            'is_admin',
            'admin' in self.roles,
        )


class SSOOAuth2Authentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            raise AuthenticationFailed("Token mal formé")

        introspect_url = os.getenv("SSO_INTROSPECT_URL", "http://host.docker.internal:8000/o/introspect/")
        client_id = os.getenv("SSO_CLIENT_ID")
        client_secret = os.getenv("SSO_CLIENT_SECRET")

        try:
            payload = {
                'token': token,
                'client_id': client_id,
                'client_secret': client_secret,
            }

            response = requests.post(introspect_url, data=payload, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('active'):
                    return (SimulatedUser(data), token)

        except Exception as e:
            print("Erreur d'introspection SSO:", e)

        raise AuthenticationFailed("Token invalide ou expiré")