# app/courses/views.py
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

# Imports de vos modules d'authentification et de permissions locaux
from courses_type.authentication import LocalJWTAuthentication
from core.permissions import IsInstructorOrAdmin
from courses.models import Course
from .serializers import CourseSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    # Intégration de votre classe d'authentification simulée par en-têtes HTTP
    authentication_classes = [LocalJWTAuthentication]

    # Intégration de la permission adaptée à votre SimulatedUser
    permission_classes = [IsInstructorOrAdmin]

    # Support des fichiers (upload) et du JSON classique
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        Optimisation de la requête (Eager Loading) :
        - select_related('category') pour la relation One-to-Many (clé étrangère simple)
        - prefetch_related('tags') pour la relation Many-to-Many (évite le problème N+1 queries)
        """
        return Course.objects.all().select_related('category').prefetch_related('tags')
