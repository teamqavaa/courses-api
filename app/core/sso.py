"""
Authentification par les tokens du SSO Qavaa.

Les access tokens sont des JWT RS256 signés par le SSO : on vérifie leur signature
avec la clé publique publiée sur /o/.well-known/jwks.json (mise en cache), ainsi que
l'émetteur (iss) et l'expiration (exp). Voir le CLAUDE.md du SSO, §6.4.
"""
import os

import jwt
from rest_framework import authentication, exceptions

SSO_ISSUER = os.getenv('SSO_ISSUER', 'https://qavaa-innovate-sso-zlvwvifuvq-ew.a.run.app').rstrip('/')
SSO_JWKS_URL = os.getenv('SSO_JWKS_URL', f'{SSO_ISSUER}/o/.well-known/jwks.json')

_jwks_client = jwt.PyJWKClient(SSO_JWKS_URL, cache_keys=True, lifespan=3600, timeout=5)

ADMIN_ROLES = {'admin', 'superadmin', 'superuser'}


def _signing_key(token):
    if jwt.get_unverified_header(token).get('kid'):
        return _jwks_client.get_signing_key_from_jwt(token).key
    # Anciens tokens émis sans "kid" : le SSO ne publie qu'une seule clé
    return _jwks_client.get_signing_keys()[0].key


def verify_sso_token(token):
    """Retourne les claims d'un token SSO valide ; lève jwt.PyJWTError sinon."""
    return jwt.decode(
        token,
        _signing_key(token),
        algorithms=['RS256'],
        issuer=SSO_ISSUER,
        options={'verify_aud': False},
    )


def get_token_from_request(request):
    """Bearer de l'en-tête Authorization, sinon cookie access_token."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[len('Bearer '):].strip() or None
    return request.COOKIES.get('access_token')


def decode_sso_request(request):
    """Claims du token de la requête ; lève AuthenticationFailed si absent ou invalide."""
    token = get_token_from_request(request)
    if not token:
        raise exceptions.AuthenticationFailed("Access token manquant.")
    try:
        return verify_sso_token(token)
    except jwt.PyJWTError:
        raise exceptions.AuthenticationFailed("Access token invalide ou expiré.")


class SSOUser:
    """Utilisateur construit depuis les claims du token SSO (pas stocké en base)."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, claims):
        self.claims = claims
        self.id = self.pk = claims.get('sub')
        self.email = claims.get('email', '')
        self.name = claims.get('name', '')
        roles = claims.get('roles') or []
        self.roles = [roles] if isinstance(roles, str) else list(roles)

    @property
    def is_admin(self):
        """Rôle admin/superadmin, ou compte is_staff / is_superuser dans le SSO."""
        return (
            bool(ADMIN_ROLES.intersection(self.roles))
            or self.claims.get('is_staff') is True
            or self.claims.get('is_superuser') is True
        )

    @property
    def is_instructor(self):
        return self.is_admin or 'instructor' in self.roles

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def role(self):
        """Rôle principal (compatibilité avec les permissions basées sur user.role)."""
        if self.is_admin:
            return 'admin'
        if 'instructor' in self.roles:
            return 'instructor'
        return self.roles[0] if self.roles else 'student'

    def __str__(self):
        return self.email or str(self.id)


class SSOAuthentication(authentication.BaseAuthentication):
    """Authentification DRF : request.user devient un SSOUser vérifié."""

    def authenticate(self, request):
        if not get_token_from_request(request):
            return None
        return SSOUser(decode_sso_request(request)), get_token_from_request(request)

    def authenticate_header(self, request):
        return 'Bearer'


class OptionalSSOAuthentication(SSOAuthentication):
    """
    Variante pour les ressources publiques (catalogue) : un token absent, expiré ou
    invalide rend la requête anonyme au lieu de la rejeter. Les écritures restent
    protégées par les permissions de la vue.
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except exceptions.AuthenticationFailed:
            return None
