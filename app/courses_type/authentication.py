from core.sso import SSOAuthentication


class LocalJWTAuthentication(SSOAuthentication):
    """
    Conservée pour compatibilité : l'utilisateur provient désormais du token SSO
    vérifié, et non plus des en-têtes X-User-Id / X-User-Role (falsifiables).
    """
