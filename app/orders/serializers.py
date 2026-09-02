from rest_framework import serializers
from .models import Order
from order_items.models import OrderItem
from courses.serializers import CourseSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des lignes de commande."""
    course = CourseSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'course', 'price_paid', 'created_at']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture d'une commande complète avec ses items."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [  # noqa: RUF012
            'id',
            'user_id',
            'user_email',
            'user_role',
            'status',
            'status_display',
            'total_amount',
            'currency',
            'discount',
            'discount_amount',
            'discount_code_snapshot',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
