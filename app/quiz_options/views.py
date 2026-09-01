from rest_framework import viewsets
from .models import QuizOption
from .serializers import QuizOptionSerializer


class QuizOptionViewSet(viewsets.ModelViewSet):
    queryset = QuizOption.objects.all()
    serializer_class = QuizOptionSerializer
