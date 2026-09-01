import os
from rest_framework import permissions
import requests
from rest_framework.permissions import BasePermission


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


""""
Validation de la permission des backends pour le SSO et le backends des cours.
"""


# core/permissions.py
# core/permissions.py
import os
import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class SimulatedUser:
    """Objet utilisateur minimaliste pour satisfaire DRF."""
    def __init__(self, user_data):
        self.id = user_data.get('sub') or user_data.get('user_id')
        self.is_authenticated = True
        # Récupérez ces rôles depuis les claims du token ou de l'introspection si le SSO les renvoie
        self.is_instructor = user_data.get('is_instructor', False)
        self.is_admin = user_data.get('is_admin', False)

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
            # Correction : Envoi des identifiants dans le payload POST
            payload = {
                'token': token,
                'client_id': client_id,
                'client_secret': client_secret,
            }

            response = requests.post(
                introspect_url,
                data=payload,
                timeout=5
            )

            print("--- DEBUG SSO INTROSPECT ---")
            print("Statut HTTP :", response.status_code)
            print("Réponse brute :", response.text)
            print("----------------------------")

            if response.status_code == 200:
                data = response.json()
                if data.get('active'):
                    # On instancie un objet utilisateur simulé exploitable par les permissions
                    user = SimulatedUser(data)
                    return (user, token)

        except Exception as e:
            print("Erreur d'introspection SSO:", e)

        raise AuthenticationFailed("Token invalide ou expiré")
