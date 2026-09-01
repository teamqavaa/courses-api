import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings


class SSOCallbackView(APIView):
    """
    Legacy OAuth2 code-exchange endpoint.

    courses-api no longer creates local users: the SSO backend issues JWTs and
    courses-api only verifies them. This view keeps the code->token exchange
    for compatibility but returns the SSO userinfo payload as-is.
    """

    def post(self, request):
        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri')

        if not code or not redirect_uri:
            return Response({'error': 'Le code et redirect_uri sont requis'}, status=400)

        token_response = requests.post(
            f"{settings.SSO_SERVER_URL}/o/token/",
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'client_id': settings.SSO_CLIENT_ID,
                'client_secret': settings.SSO_CLIENT_SECRET,
            }
        )

        if token_response.status_code != 200:
            return Response({'error': 'Code invalide ou expiré'}, status=400)

        access_token = token_response.json().get('access_token')

        user_info_resp = requests.get(
            f"{settings.SSO_SERVER_URL}/o/userinfo/",
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if user_info_resp.status_code != 200:
            return Response({'error': 'Impossible de récupérer les informations utilisateur SSO'}, status=400)

        return Response({
            'access': access_token,
            'user': user_info_resp.json(),
        })