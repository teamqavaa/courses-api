import jwt
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
from carts.models import Cart
from orders.services import CheckoutService


@method_decorator(csrf_exempt, name='dispatch')
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = OrderSerializer

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
            return Order.objects.all().prefetch_related('items__course')

        if user_id:
            return Order.objects.filter(user_id=user_id).prefetch_related('items__course')

        return Order.objects.none()

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        user_id, user_email, user_role = self._get_user_info_from_request(request)

        if not user_id:
            return Response({"detail": "Utilisateur non authentifié ou token invalide."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            cart = Cart.objects.get(user_id=user_id)
        except Cart.DoesNotExist:
            return Response({"detail": "Panier non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({"detail": "Votre panier est vide."}, status=status.HTTP_400_BAD_REQUEST)

        order = CheckoutService.create_order_from_cart(cart)

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
