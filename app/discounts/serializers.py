# app/discounts/serializers.py
from rest_framework import serializers
from .models import Discount
from courses.serializers import CourseSerializer


class DiscountSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Discount.
    Utilisé pour l'administration des coupons et la vérification par les étudiants.
    """
    # Inclut les détails du cours ciblé en lecture seule (pour le frontend)
    course_details = CourseSerializer(source='course', read_only=True)

    # Expose la propriété dynamique définie dans le modèle
    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = Discount
        fields = [  # noqa: RUF012
            'id',
            'code',
            'discount_percentage',
            'course',
            'course_details',
            'active',
            'valid_from',
            'valid_to',
            'max_uses',
            'used_count',
            'is_valid',
            'created_at',
        ]
        read_only_fields = ['id', 'used_count', 'is_valid', 'created_at']  # noqa: RUF012

    def validate_code(self, value: str) -> str:
        """
        Nettoie et force le code en majuscules (ex: 'welcome2026' -> 'WELCOME2026').
        """
        return value.strip().upper()

    def validate(self, attrs):
        """
        Validations croisées :
        - S'assure que la date de fin est postérieure à la date de début.
        """
        valid_from = attrs.get('valid_from', getattr(self.instance, 'valid_from', None))
        valid_to = attrs.get('valid_to', getattr(self.instance, 'valid_to', None))

        if valid_from and valid_to and valid_from >= valid_to:
            raise serializers.ValidationError({
                "valid_to": "La date de fin ('valid_to') doit être postérieure à la date de début ('valid_from')."
            })

        return attrs


class ApplyDiscountSerializer(serializers.Serializer):
    """
    Sérialiseur simplifié utilisé lorsqu'un étudiant soumet un code promo dans son panier.
    """
    code = serializers.CharField(max_length=50, required=True)

    def validate_code(self, value: str) -> str:
        return value.strip().upper()
