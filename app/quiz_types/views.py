from rest_framework import viewsets
from .models import TypeQuiz
from .serializers import TypeQuizSerializer


class TypeQuizViewSet(viewsets.ModelViewSet):
    queryset = TypeQuiz.objects.all()
    serializer_class = TypeQuizSerializer
