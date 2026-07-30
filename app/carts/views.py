# carts/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from .models import Cart
from cart_items.models import CartItem
from .serializers import CartSerializer
from courses.models import Course


class CartViewSet(viewsets.GenericViewSet):
    """
    ViewSet pour la gestion du panier utilisateur.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get_cart(self, user):
        """Récupère le panier de l'utilisateur ou en crée un s'il n'existe pas."""
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    @action(detail=False, methods=['get'], url_path='my-cart')
    def my_cart(self, request):
        """
        GET /api/carts/my-cart/
        Affiche le contenu du panier et le prix total.
        """
        cart = self.get_cart(request.user)
        # Optimisation des requêtes SQL avec prefetch_related
        cart_queryset = Cart.objects.filter(id=cart.id).prefetch_related('items__course').first()
        serializer = self.get_serializer(cart_queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        """
        POST /api/carts/add-item/
        Body: { "course_id": <int> }
        Ajoute un cours au panier.
        """
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"detail": "Le champ 'course_id' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Ce cours n'existe pas."},
                status=status.HTTP_404_NOT_FOUND
            )

        cart = self.get_cart(request.user)

        # Vérification si le cours est déjà dans le panier
        if CartItem.objects.filter(cart=cart, course=course).exists():
            return Response(
                {"detail": "Ce cours est déjà dans votre panier."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Création de l'élément avec exécution des validations du modèle (clean())
        try:
            cart_item = CartItem(cart=cart, course=course)
            cart_item.save()  # Déclenche cart_item.full_clean() défini dans votre modèle
        except ValidationError as e:
            return Response(
                {"detail": e.messages[0] if hasattr(e, 'messages') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "Cours ajouté au panier avec succès."},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['delete'], url_path='remove-item')
    def remove_item(self, request):
        """
        DELETE /api/carts/remove-item/
        Body: { "course_id": <int> }  ou query param ?course_id=<int>
        Supprime un cours du panier.
        """
        course_id = request.data.get('course_id') or request.query_params.get('course_id')

        if not course_id:
            return Response(
                {"detail": "Le champ 'course_id' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self.get_cart(request.user)

        try:
            cart_item = CartItem.objects.get(cart=cart, course_id=course_id)
            cart_item.delete()
            return Response(
                {"detail": "Le cours a été retiré du panier."},
                status=status.HTTP_200_OK
            )
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Ce cours ne se trouve pas dans votre panier."},
                status=status.HTTP_404_NOT_FOUND
            )


