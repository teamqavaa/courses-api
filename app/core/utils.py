from rest_framework.exceptions import AuthenticationFailed

from core.sso import decode_sso_request


def get_user_sub_from_request(request):
    """
    Retourne le 'sub' (UUID de l'utilisateur SSO) du token de la requête
    (en-tête Authorization Bearer ou cookie access_token), après vérification
    de sa signature.
    """
    user_sub = decode_sso_request(request).get('sub')
    if not user_sub:
        raise AuthenticationFailed("Le champ 'sub' est absent du token.")
    return str(user_sub)
