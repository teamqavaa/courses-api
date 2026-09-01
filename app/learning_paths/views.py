from django.db.models import Prefetch

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from courses.models import Course
from courses.serializers import CourseListItemSerializer

from .models import LearningPath
from .serializers import LearningPathDetailSerializer, LearningPathSerializer


PUBLISHED = 'published'


class LearningPathViewSet(viewsets.ModelViewSet):
    """
    ViewSet that handles full CRUD for LearningPath:
    - CREATE (POST)
    - READ (GET list + GET details)
    - UPDATE (PUT & PATCH)
    - DELETE (DELETE)

    Custom endpoints:
    - GET /api/learning-paths/active/ returns only active paths, optional ?kind=skill|career
    - GET /api/learning-paths/{slug}/courses/ returns the active courses attached to a path
    - GET /api/learning-paths/{slug}/detail/ returns path + bullets + courses in one payload

    `lookup_field='slug'` matches the dashboard, which keys every path URL on
    the slug (the LearningPathSerializer exposes `id` as the slug).
    """
    queryset = LearningPath.objects.all()
    serializer_class = LearningPathSerializer
    lookup_field = 'slug'

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """Return only learning paths where is_active=True, optionally filtered by ?kind=."""
        active_paths = (
            LearningPath.objects.filter(is_active=True)
            .prefetch_related('courses')
        )
        kind = request.query_params.get('kind')
        if kind:
            active_paths = active_paths.filter(kind=kind)
        serializer = self.get_serializer(active_paths, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='courses')
    def courses(self, request, *args, **kwargs):
        """Return only the published courses attached to this learning path."""
        path = self.get_object()
        active_courses = path.courses.filter(status=PUBLISHED).prefetch_related(
            'highlights',
            'outcomes',
            'learning_points',
            'requirements',
            'modules',
            'modules__lessons',
            'resources',
        )
        serializer = CourseListItemSerializer(active_courses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='detail')
    def path_detail(self, request, *args, **kwargs):
        """Return the path with its outcomes, prerequisites and published courses.

        Method must NOT be named `detail`: DRF reserves `detail` as a viewset
        attribute (router injects `detail=True`), which shadows the action.
        """
        path = (
            LearningPath.objects.filter(slug=kwargs.get('slug'))
            .prefetch_related(
                'outcomes',
                'prerequisites',
                Prefetch(
                    'courses',
                    queryset=Course.objects.filter(status=PUBLISHED).prefetch_related(
                        'highlights',
                        'outcomes',
                        'learning_points',
                        'requirements',
                        'modules',
                        'modules__lessons',
                        'resources',
                    ),
                ),
            )
            .first()
        )
        if path is None:
            raise NotFound()
        serializer = LearningPathDetailSerializer(path)
        return Response(serializer.data)