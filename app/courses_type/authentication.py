# app/courses/authentication.py
from rest_framework import authentication
from rest_framework import exceptions

class SimulatedUser:
    def __init__(self, user_id, email, role):
        self.id = user_id
        self.email = email
        self.role = role
        self.is_authenticated = True

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_instructor(self):
        return self.role in ["admin", "instructor"]


class LocalJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # On ne cherche plus un JWT, on cherche directement des headers en clair !
        user_id = request.headers.get("X-User-Id")
        role = request.headers.get("X-User-Role", "student")
        email = request.headers.get("X-User-Email", "user@test.com")

        # Si le header X-User-Id n'est pas fourni, on considère l'utilisateur comme anonyme
        if not user_id:
            return None

        # On instancie notre utilisateur simulé
        user = SimulatedUser(user_id=user_id, email=email, role=role)
        return (user, None)
