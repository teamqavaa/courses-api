import uuid
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get('sub') or validated_token.get('user_id')
        email = validated_token.get('email')

        if not user_id:
            return None

        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError:
            return None

        # On instancie l'utilisateur en mémoire SANS l'enregistrer en base de données
        user = User(
            id=user_uuid,
            email=email or '',
            username=email or str(user_uuid)
        )
        return user
