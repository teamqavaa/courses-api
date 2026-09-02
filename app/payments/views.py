# app/payments/views.py
import jwt
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, PaymentProvider
from .serializers import (
    PaymentSerializer,
    PaymentProviderSerializer,
    InitiatePaymentSerializer
)
from .services import PaymentService


class PaymentProviderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = PaymentProviderSerializer
    queryset = PaymentProvider.objects.filter(is_active=True)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = PaymentSerializer

    def _get_user_info_from_request(self, request):
        token = request.COOKIES.get("access_token")
        if not token:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")

        if not token:
            return None, None, None

        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            email = payload.get("email")
            roles = payload.get("roles", [])

            role = None
            if isinstance(roles, list) and roles:
                if "superadmin" in roles:
                    role = "superadmin"
                elif "admin" in roles:
                    role = "admin"
                else:
                    role = roles[0]
            elif isinstance(roles, str):
                role = roles

            return user_id, email, role
        except jwt.PyJWTError:
            return None, None, None

    def get_queryset(self):
        user_id, email, role = self._get_user_info_from_request(self.request)

        if role in ["admin", "superadmin"]:
            return Payment.objects.all().select_related('order', 'provider')

        if user_id:
            # Assurez-vous que votre modèle Order utilise user_id ou user selon votre architecture
            return Payment.objects.filter(order__user_id=user_id).select_related('order', 'provider')

        return Payment.objects.none()

    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate(self, request):
        user_id, _, _ = self._get_user_info_from_request(request)

        if not user_id:
            return Response({"detail": "Utilisateur non authentifié ou token invalide."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = InitiatePaymentSerializer(
            data=request.data,
            context={'request': request, 'user_id': user_id}
        )
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.initiate_payment(
            order_id=serializer.validated_data['order_id'],
            provider_code=serializer.validated_data['provider_code']
        )

        return Response(self.get_serializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentWebhookAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, provider_code, *args, **kwargs):
        success = PaymentService.process_webhook(
            provider_code=provider_code.upper(),
            request=request
        )

        if success:
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        return Response(
            {"detail": "Webhook processing failed or signature invalid."},
            status=status.HTTP_400_BAD_REQUEST
        )
