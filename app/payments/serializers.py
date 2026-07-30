from rest_framework import serializers
from payments.models import Payment
from payment_providers.models import PaymentProvider
from orders.models import Order


class PaymentProviderSerializer(serializers.ModelSerializer):
    """
    Serializer pour exposer les prestataires de paiement disponibles au Frontend.
    Exclut volontairement le champ 'config' (clés API) pour des raisons de sécurité.
    """
    class Meta:
        model = PaymentProvider
        fields = ['id', 'name', 'code', 'is_active', 'logo']  # noqa: RUF012
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture du détail d'un paiement effectué ou en cours.
    """
    provider = PaymentProviderSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = [  # noqa: RUF012
            'id',
            'order',
            'provider',
            'status',
            'status_display',
            'amount',
            'currency',
            'transaction_reference',
            'client_secret',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class InitiatePaymentSerializer(serializers.Serializer):
    """
    Serializer d'entrée pour initier un paiement depuis le Frontend.
    Demande l'ID de la commande (Order) et le code du prestataire choisi.
    """
    order_id = serializers.UUIDField(
        required=True,
        help_text="UUID de la commande (Order) à payer"
    )
    provider_code = serializers.ChoiceField(
        choices=PaymentProvider.ProviderCode.choices,
        required=True,
        help_text="Code du prestataire sélectionné (ex: WAVE, STRIPE, ORANGE_MONEY)"
    )

    def validate_order_id(self, value):
        """Vérifie que la commande existe et appartient à l'utilisateur connecté."""
        user = self.context['request'].user
        try:
            order = Order.objects.get(id=value, user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Commande introuvable ou ne vous appartient pas.")

        if order.status == Order.OrderStatus.PAID:
            raise serializers.ValidationError("Cette commande a déjà été payée.")

        if order.status == Order.OrderStatus.CANCELLED:
            raise serializers.ValidationError("Impossible de payer une commande annulée.")

        return value

    def validate_provider_code(self, value):
        """Vérifie que le prestataire existe et est actif."""
        try:
            provider = PaymentProvider.objects.get(code=value)
        except PaymentProvider.DoesNotExist:
            raise serializers.ValidationError("Prestataire de paiement introuvable.")

        if not provider.is_active:
            raise serializers.ValidationError("Ce moyen de paiement est actuellement indisponible.")

        return value

