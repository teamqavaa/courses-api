# app/discounts/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Discount
from .serializers import DiscountSerializer, ApplyDiscountSerializer


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Permission sur-mesure :
    - Seuls les administrateurs (is_staff=True ou role='ADMIN') ont un accès total (CRUD).
    - Les requêtes sont bloquées pour les utilisateurs ordinaires (sauf sur les actions personnalisées).
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Vérifie si l'utilisateur est admin ou staff
        is_admin = request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN'
        return is_admin


class DiscountViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des coupons/réductions :
    - CRUD complet réservé aux Administrateurs.
    - Action `validate_coupon` accessible à tous les étudiants connectés.
    """
    queryset = Discount.objects.all().select_related('course').order_by('-created_at')
    serializer_class = DiscountSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    @action(
        detail=False,
        methods=['post'],
        url_path='validate',
        permission_classes=[IsAuthenticated]
    )
    def validate_coupon(self, request):
        """
        Endpoint d'aide pour le frontend (Next.js) :
        POST /api/discounts/validate/
        Body: { "code": "WELCOME2026" }

        Vérifie la validité d'un code sans encore l'attacher au panier.
        """
        serializer = ApplyDiscountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']

        try:
            discount = Discount.objects.select_related('course').get(code=code)
        except Discount.DoesNotExist:
            return Response(
                {"detail": "Code promo invalide."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not discount.is_valid:
            return Response(
                {"detail": "Ce code promo a expiré ou n'est plus disponible."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Réponse structurée pour le frontend
        return Response(
            {
                "detail": "Code promo valide.",
                "discount": DiscountSerializer(discount).data
            },
            status=status.HTTP_200_OK
        )
