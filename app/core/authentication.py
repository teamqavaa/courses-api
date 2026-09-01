import uuid

from rest_framework_simplejwt.authentication import JWTAuthentication


class ClaimUser:
    """
    In-memory user built from the claims of an SSO-issued JWT.

    courses-api deliberately keeps no local user rows: the SSO backend is the
    single source of truth, and `sub` (a UUID) is the stable cross-service
    identifier used by progress, enrollments and learning paths.
    """

    def __init__(self, claims):
        self.id = str(claims.get('sub') or claims.get('user_id') or '')
        try:
            self.id = str(uuid.UUID(self.id))
        except (ValueError, TypeError):
            pass
        self.pk = self.id
        self.email = claims.get('email') or ''
        self.roles = claims.get('roles') or []
        self.is_authenticated = True
        self.is_active = True

    @property
    def is_admin(self):
        return 'admin' in self.roles

    @property
    def is_instructor(self):
        return 'admin' in self.roles or 'instructor' in self.roles

    @property
    def is_staff(self):
        return 'staff' in self.roles or self.is_admin

    @property
    def is_superuser(self):
        return self.is_admin

    def __str__(self):
        return self.email or self.id


class CustomJWTAuthentication(JWTAuthentication):
    """
    Verifies RS256 JWTs signed by the SSO backend (public key only) and maps
    the claims (sub / email / roles) to a ClaimUser without touching the DB.
    """

    def get_user(self, validated_token):
        claims = validated_token.payload
        if not (claims.get('sub') or claims.get('user_id')):
            return None
        return ClaimUser(claims)