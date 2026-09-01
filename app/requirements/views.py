from rest_framework import viewsets

from .models import CourseRequirement
from .serializers import CourseRequirementSerializer


class CourseRequirementViewSet(viewsets.ModelViewSet):
    queryset = CourseRequirement.objects.all()
    serializer_class = CourseRequirementSerializer
