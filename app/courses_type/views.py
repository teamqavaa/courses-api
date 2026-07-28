# views.py
from rest_framework import viewsets
from .models import TypeCourse
from .serializers import TypeCourseSerializer
from .authentication import LocalJWTAuthentication
from rest_framework import permissions

class TypeCourseViewSet(viewsets.ModelViewSet):
    """
    Ce ViewSet gère automatiquement tout le CRUD pour TypeCourse :
    - CREATE (POST)
    - READ (GET liste + GET détails)
    - UPDATE (PUT & PATCH)
    - DELETE (DELETE)
    """
    queryset = TypeCourse.objects.all()
    serializer_class = TypeCourseSerializer

    # On applique notre authentification JWT locale
    authentication_classes = [LocalJWTAuthentication]

    def get_permissions(self):
        # Tout le monde peut lister et voir les détails
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]

        # Pour POST, PUT, DELETE, l'utilisateur doit être authentifié et admin
        # (Pour ce test simple, nous utilisons la classe IsAdminUser de DRF personnalisée ou par défaut)
        return [permissions.IsAuthenticated()]

