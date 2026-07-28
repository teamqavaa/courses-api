# app/enrollments/views.py
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .models import Enrollment
from .serializers import EnrollmentSerializer

class EnrollmentViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    ViewSet permettant à l'étudiant connecté de l'API de :
    - Lister ses inscriptions actives (GET /api/enrollments/)
    - Voir le détail d'une inscription spécifique (GET /api/enrollments/{id}/)
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Sécurité cruciale : l'utilisateur ne peut voir QUE ses propres inscriptions
        return Enrollment.objects.filter(
            user=self.request.user,
            status='active'
        ).select_related('course') # Optimisation SQL pour joindre la table Course
