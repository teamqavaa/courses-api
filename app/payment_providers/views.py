import jwt
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from .models import PaymentProvider
from .serializers import PaymentProviderSerializer


class PaymentProviderViewSet(viewsets.ModelViewSet):
    """
    API CRUD complète pour les prestataires de paiement.
    Lecture ouverte à tous, mais écriture réservée aux admins/superadmins via le SSO.
    """
    queryset = PaymentProvider.objects.all()
    serializer_class = PaymentProviderSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def _get_user_info_from_request(self, request):
        token = request.COOKIES.get("access_token")
        if not token:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")

        if not token:
            return None, False

        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            roles = payload.get("roles", [])

            is_admin = False
            if isinstance(roles, list):
                if "superadmin" in roles or "admin" in roles:
                    is_admin = True
            elif isinstance(roles, str) and roles in ["admin", "superadmin"]:
                is_admin = True

            return user_id, is_admin
        except jwt.PyJWTError:
            return None, False

    def create(self, request, *args, **kwargs):
        user_id, is_admin = self._get_user_info_from_request(request)
        if not is_admin:
            return Response(
                {"detail": "Action réservée aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data, context={'user_id': user_id})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        _, is_admin = self._get_user_info_from_request(request)
        if not is_admin:
            return Response(
                {"detail": "Action réservée aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        _, is_admin = self._get_user_info_from_request(request)
        if not is_admin:
            return Response(
                {"detail": "Action réservée aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
