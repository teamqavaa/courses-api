import jwt
from rest_framework.exceptions import AuthenticationFailed

def get_user_sub_from_request(request):
    """
    Extrait et décode le 'sub' du cookie access_token ou de l'en-tête Authorization.
    """
    access_token = request.COOKIES.get('access_token')

    if not access_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]

    if not access_token:
        raise AuthenticationFailed("Access token manquant dans les cookies.")

    try:
        payload = jwt.decode(access_token, options={"verify_signature": False})
        user_sub = payload.get('sub')

        if not user_sub:
            raise AuthenticationFailed("Le champ 'sub' est absent du token.")

        return str(user_sub)
    except jwt.PyJWTError:
        raise AuthenticationFailed("Access token invalide.")
