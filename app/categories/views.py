from rest_framework import viewsets, permissions
from .models import Category
from .serializers import CategorySerializer
from courses_type.authentication import LocalJWTAuthentication  # Votre authentification personnalisée
from core.authentication import CustomJWTAuthentication


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [CustomJWTAuthentication, LocalJWTAuthentication]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Si on liste toutes les catégories, on ne prend que les catégories "racines" (sans parent).
        # Les sous-catégories seront incluses récursivement à l'intérieur de ces racines.
        if self.action == 'list':
            return queryset.filter(parent__isnull=True)
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
