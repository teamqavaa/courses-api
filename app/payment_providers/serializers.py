from rest_framework import serializers
from .models import PaymentProvider


class PaymentProviderSerializer(serializers.ModelSerializer):
    """
    Serializer pour le CRUD des prestataires de paiement.
    Gère la validation, l'exposition des données et l'injection automatique du user_id créateur.
    """
    user_id = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = PaymentProvider
        fields = [
            'id',
            'name',
            'code',
            'is_active',
            'logo',
            'config',
            'user_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']

    def validate_code(self, value):
        """Vérifie que le code fourni fait bien partie des choix autorisés."""
        if value not in PaymentProvider.ProviderCode.values:
            raise serializers.ValidationError(f"Le code '{value}' n'est pas un prestataire de paiement valide.")
        return value

    def create(self, validated_data):
        """Injecte automatiquement le user_id récupéré du contexte SSO lors de la création."""
        user_id = self.context.get('user_id')
        if user_id:
            validated_data['user_id'] = user_id
        return super().create(validated_data)
