# app/payments/serializers.py
from rest_framework import serializers
from payments.models import Payment
from payment_providers.models import PaymentProvider
from orders.models import Order


class PaymentProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProvider
        ref_name = 'PaymentsPaymentProvider'  # <-- Empêche la collision Swagger avec l'app 'payment_providers'
        fields = ['id', 'name', 'code', 'is_active', 'logo']
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    provider = PaymentProviderSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
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
    order_id = serializers.UUIDField(
        required=True,
        help_text="UUID de la commande (Order) à payer"
    )
    provider_code = serializers.CharField(
        required=True,
        help_text="Code du prestataire sélectionné (ex: QAVAA, IGNITE)"
    )

    def validate_order_id(self, value):
        user_id = self.context.get('user_id')
        try:
            order = Order.objects.get(id=value, user_id=user_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Commande introuvable ou ne vous appartient pas.")

        if order.status == Order.OrderStatus.PAID:
            raise serializers.ValidationError("Cette commande a déjà été payée.")

        if order.status == Order.OrderStatus.CANCELLED:
            raise serializers.ValidationError("Impossible de payer une commande annulée.")

        return value

    def validate_provider_code(self, value):
        try:
            provider = PaymentProvider.objects.get(code=value.upper())
        except PaymentProvider.DoesNotExist:
            raise serializers.ValidationError("Prestataire de paiement introuvable.")

        if not provider.is_active:
            raise serializers.ValidationError("Ce moyen de paiement est actuellement indisponible.")

        return value.upper()
