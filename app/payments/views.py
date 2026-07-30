# app/payments/views.py
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
    """
    API en lecture seule pour récupérer la liste des prestataires de paiement actifs.
    - GET /api/payments/providers/
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PaymentProviderSerializer
    queryset = PaymentProvider.objects.filter(is_active=True)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour consulter l'historique de ses paiements et initier un règlement.
    - GET  /api/payments/      : Historique des paiements de l'utilisateur
    - GET  /api/payments/{id}/ : Détail d'un paiement
    - POST /api/payments/initiate/ : Inicie une session de paiement avec le provider
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        """Un utilisateur ne peut voir QUE les paiements associés à ses propres commandes."""
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all().select_related('order', 'provider')
        return Payment.objects.filter(order__user=user).select_related('order', 'provider')

    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate(self, request):
        """
        Déclenche une tentative de paiement pour une commande donnée.
        Payload attendu: { "order_id": "UUID", "provider_code": "WAVE|STRIPE|..." }
        """
        serializer = InitiatePaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order_id']
        provider_code = serializer.validated_data['provider_code']

        # Appel du service métier pour initialiser le paiement auprès de la passerelle
        payment = PaymentService.initiate_payment(
            order_id=order_id,
            provider_code=provider_code
        )

        response_serializer = self.get_serializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PaymentWebhookAPIView(APIView):
    """
    Endpoint recevant les notifications asynchrones (Webhooks) des prestataires (Stripe, Wave, OM).
    - POST /api/payments/webhook/{provider_code}/
    Avis : Cet endpoint est ouvert (AllowAny) car appelé par les serveurs externes des prestataires.
    La sécurité est assurée par la vérification de la signature dans le PaymentService.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, provider_code, *args, **kwargs):
        provider_code_upper = provider_code.upper()

        # Traitement du Webhook via le service métier
        success = PaymentService.process_webhook(
            provider_code=provider_code_upper,
            request=request
        )

        if success:
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        return Response(
            {"detail": "Webhook processing failed or signature invalid."},
            status=status.HTTP_400_BAD_REQUEST
        )
