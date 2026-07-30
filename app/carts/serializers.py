# carts/serializers.py
from rest_framework import serializers
from carts.models import Cart
from cart_items.models import CartItem
from courses.serializers import CourseSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Sérialiseur pour chaque ligne du panier."""
    # Inclut les détails lisibles du cours (titre, image, etc.)
    course_details = CourseSerializer(source='course', read_only=True)
    # Expose la propriété 'price' définie dans le modèle CartItem
    price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'course', 'course_details', 'price', 'added_at']  # noqa: RUF012
        read_only_fields = ['id', 'price', 'added_at']  # noqa: RUF012


class CartSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le panier complet."""
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    items_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'items_count', 'total_price', 'created_at', 'updated_at']  # noqa: RUF012
        read_only_fields = ['id', 'user', 'items', 'items_count', 'total_price', 'created_at', 'updated_at']  # noqa: RUF012


