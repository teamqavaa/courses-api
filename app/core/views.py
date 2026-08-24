import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class SSOCallbackView(APIView):
    def post(self, request):
        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri')

        if not code or not redirect_uri:
            return Response({'error': 'Le code et redirect_uri sont requis'}, status=400)

        # 1. Échanger le code contre les identifiants SSO
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

        # 2. Récupérer les infos de l'utilisateur depuis le SSO (f-string corrigée ici)
        user_info_resp = requests.get(
            f"{settings.SSO_SERVER_URL}/o/userinfo/",
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if user_info_resp.status_code != 200:
            return Response({'error': 'Impossible de récupérer les informations utilisateur SSO'}, status=400)

        user_data = user_info_resp.json()

        # 3. Récupérer ou créer l'utilisateur localement dans l'App A
        username = user_data.get('username') or user_data.get('sub')
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={'email': user_data.get('email', '')}
        )

        # 4. Générer des tokens SimpleJWT pour l'App A
        local_refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(local_refresh.access_token),
            'refresh': str(local_refresh),
        })
