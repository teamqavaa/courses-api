import jwt
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from django.core.exceptions import ValidationError

from .models import Cart
from cart_items.models import CartItem
from .serializers import CartSerializer
from courses.models import Course


class CartViewSet(viewsets.GenericViewSet):
    """
    ViewSet pour la gestion du panier utilisateur via SSO (cookie access_token).
    """
    serializer_class = CartSerializer
    permission_classes = []  # Désactive toute vérification de permission DRF sur ce ViewSet
    authentication_classes = []  # Désactive l'authentification DRF globale sur ce ViewSet

    def _resolve_access_token(self, request):
        """Extrait le token depuis l'en-tête Authorization (Bearer) ou le cookie access_token."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[len('Bearer '):].strip()

        return request.COOKIES.get('access_token')

    def get_cart(self, request):
        """Récupère ou crée le panier basé sur le 'sub' extrait du token access (Bearer ou cookie)."""
        access_token = self._resolve_access_token(request)

        if not access_token:
            raise AuthenticationFailed("Access token manquant (Bearer ou cookie).")

        try:
            payload = jwt.decode(access_token, options={"verify_signature": False})
            user_sub = payload.get('sub')

            if not user_sub:
                raise AuthenticationFailed("Le champ 'sub' est absent du token.")

        except jwt.PyJWTError:
            raise AuthenticationFailed("Access token invalide.")

        cart, _ = Cart.objects.get_or_create(user_id=str(user_sub))
        return cart

    @action(detail=False, methods=['get'], url_path='my-cart')
    def my_cart(self, request):
        """
        GET /api/carts/my-cart/
        Affiche le contenu du panier et le prix total.
        """
        cart = self.get_cart(request)
        cart_queryset = Cart.objects.filter(id=cart.id).prefetch_related('items__course').first()
        serializer = self.get_serializer(cart_queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        """
        POST /api/carts/add-item/
        Body: { "course_id": <slug> }
        Ajoute un cours au panier. Le cours est identifié par son slug
        (cohérent avec le reste de l'API, ex. /api/my/progress/<slug>/).
        """
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"detail": "Le champ 'course_id' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(slug=course_id)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Ce cours n'existe pas."},
                status=status.HTTP_404_NOT_FOUND
            )

        cart = self.get_cart(request)

        if CartItem.objects.filter(cart=cart, course=course).exists():
            return Response(
                {"detail": "Ce cours est déjà dans votre panier."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart_item = CartItem(cart=cart, course=course)
            cart_item.save()
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
        Body: { "course_id": <slug> } ou query param ?course_id=<slug>
        Supprime un cours du panier. Le cours est identifié par son slug.
        """
        course_id = request.data.get('course_id') or request.query_params.get('course_id')

        if not course_id:
            return Response(
                {"detail": "Le champ 'course_id' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self.get_cart(request)

        try:
            course = Course.objects.get(slug=course_id)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Ce cours n'existe pas."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            cart_item = CartItem.objects.get(cart=cart, course=course)
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
