# app/orders/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
from carts.models import Cart
from orders.services import CheckoutService


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pour consulter l'historique des commandes et effectuer le checkout.
    - GET  /api/orders/      : Liste les commandes de l'utilisateur connecté
    - GET  /api/orders/{id}/ : Détail d'une commande
    - POST /api/orders/checkout/ : Valide le panier et crée la commande
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        """Un utilisateur ne peut voir QUE ses propres commandes."""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().prefetch_related('items__course')
        return Order.objects.filter(user=user).prefetch_related('items__course')

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """
        Action personnalisée pour transformer le panier (Cart) en commande (Order).
        """
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"detail": "Panier non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({"detail": "Votre panier est vide."}, status=status.HTTP_400_BAD_REQUEST)

        # Transformation du Panier en Commande via le service métier
        order = CheckoutService.create_order_from_cart(cart)

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
