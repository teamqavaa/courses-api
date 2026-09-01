# app/courses/views_tags.py
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from courses_type.authentication import LocalJWTAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.permissions import IsInstructorOrAdmin
from .models import Tag
from .serializers import TagSerializer


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les Tags.
    - GET /api/tags/ : Accessible à tous (Public).
    - POST/PUT/PATCH/DELETE : Réservé aux Instructeurs et Admins.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    authentication_classes = [JWTAuthentication, LocalJWTAuthentication]
    permission_classes = [IsInstructorOrAdmin]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
