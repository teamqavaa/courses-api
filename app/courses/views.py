from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import AuthenticationFailed

from courses.models import Course
from enrollments.models import Enrollment
from .serializers import CourseSerializer
from core.utils import get_user_sub_from_request # Votre utilitaire

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'slug'
    authentication_classes = []  # Désactivé pour uniformiser avec le Panier
    permission_classes = []      # Désactivé (géré manuellement ou par action si besoin)
    parser_classes = [MultiPartParser, FormParser, JSONParser]


    def get_queryset(self):
        return Course.objects.all().select_related('category').prefetch_related(
            'tags',
            'highlights',
            'learning_points',
            'outcomes',
            'modules__lessons__video',
            'modules__lessons__resources',
            'modules__resources',
            'resources'
        )


    @action(detail=False, methods=['get'], url_path='my-enrollments')
    def my_enrollments(self, request):
        """
        GET /api/courses/my-enrollments/
        """
        try:
            current_user_id = get_user_sub_from_request(request)
        except AuthenticationFailed as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        # Récupère les IDs des cours liés aux inscriptions de l'utilisateur
        enrolled_course_ids = Enrollment.objects.filter(user_id=current_user_id).values_list('course_id', flat=True)
        courses = self.get_queryset().filter(id__in=enrolled_course_ids)

        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
