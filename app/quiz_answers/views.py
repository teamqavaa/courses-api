from rest_framework import viewsets
from .models import QuizAnswer
from .serializers import QuizAnswerSerializer


class QuizAnswerViewSet(viewsets.ModelViewSet):
    queryset = QuizAnswer.objects.all()
    serializer_class = QuizAnswerSerializer
