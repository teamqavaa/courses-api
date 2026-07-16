# views.py
from rest_framework import viewsets
from .models import TypeCourse
from .serializers import TypeCourseSerializer

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
