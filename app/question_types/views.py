from rest_framework import viewsets
from .models import TypeQuestion
from .serializers import TypeQuestionSerializer


class TypeQuestionViewSet(viewsets.ModelViewSet):
    queryset = TypeQuestion.objects.all()
    serializer_class = TypeQuestionSerializer
