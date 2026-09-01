# app/courses/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

# Imports de vos modules d'authentification et de permissions locaux
from courses_type.authentication import LocalJWTAuthentication
from core.authentication import CustomJWTAuthentication
from core.permissions import IsInstructorOrAdmin
from courses.models import Course
from lessons.models import Lesson
from modules.models import Module
from .serializers import CourseListItemSerializer, CourseSerializer


PUBLISHED = 'published'


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    # Utilise le champ 'slug' au lieu de la clé primaire (id/pk) pour les URLs de détail
    lookup_field = 'slug'

    # Vérifie les tokens RS256 émis par le SSO (certificat public) OU accepte
    # l'authentification simulée par en-têtes HTTP pour le développement local.
    authentication_classes = [CustomJWTAuthentication, LocalJWTAuthentication]

    # Intégration de la permission adaptée à votre SimulatedUser
    permission_classes = [IsInstructorOrAdmin]

    # Support des fichiers (upload) et du JSON classique
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        Optimisation de la requête (Eager Loading) :
        - select_related('category') pour la relation One-to-Many (clé étrangère simple)
        - prefetch_related pour les relations utilisées par les sérialiseurs
          (tags, modules/leçons, bullets et ressources).
        """
        return Course.objects.all().select_related('category').prefetch_related(
            'tags',
            'modules',
            'modules__lessons',
            'resources',
            'highlights',
            'outcomes',
            'learning_points',
            'requirements',
        )

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """GET /api/courses/active/ - the published catalog for the dashboard."""
        courses = self.get_queryset().filter(status=PUBLISHED)
        serializer = CourseListItemSerializer(courses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='curriculum')
    def curriculum(self, request, *args, **kwargs):
        """GET /api/courses/{slug}/curriculum/ - published modules + lessons."""
        course = self.get_object()
        modules = (
            Module.objects.filter(course=course, is_published=True)
            .order_by('order')
            .prefetch_related('lessons')
        )

        module_data = []
        total_lessons = 0
        total_duration = 0
        for module in modules:
            lessons = sorted(
                [lesson for lesson in module.lessons.all() if lesson.is_published],
                key=lambda lesson: lesson.order,
            )
            total_lessons += len(lessons)
            total_duration += sum(lesson.duration_in_minutes for lesson in lessons)

            if not lessons:
                continue

            module_data.append({
                'id': str(module.pk),
                'title': module.title,
                'order': module.order,
                'lessons': [
                    {
                        'id': str(lesson.pk),
                        'title': lesson.title,
                        'order': lesson.order,
                        'lesson_type': lesson.lesson_type.lower(),
                        'duration_minutes': lesson.duration_in_minutes,
                    }
                    for lesson in lessons
                ],
            })

        return Response({
            'course_id': course.slug,
            'total_lessons': total_lessons,
            'total_duration_minutes': total_duration,
            'modules': module_data,
        })

    @action(detail=True, methods=['get'], url_path='path-context')
    def path_context(self, request, *args, **kwargs):
        """GET /api/courses/{slug}/path-context/ - the learning paths a course belongs to."""
        from learning_paths.models import LearningPath

        course = self.get_object()
        paths = LearningPath.objects.filter(courses=course, is_active=True).order_by('order', 'title')

        result = []
        for path in paths:
            active_courses = sorted(
                [item for item in path.courses.all() if item.status == PUBLISHED],
                key=lambda item: item.id,
            )
            try:
                position = next(
                    i for i, item in enumerate(active_courses, start=1)
                    if str(item.id) == str(course.id)
                )
            except StopIteration:
                position = None

            result.append({
                'id': path.slug,
                'title': path.title,
                'slug': path.slug,
                'kind': path.kind,
                'position': position,
                'total_courses': len(active_courses),
            })

        return Response({'paths': result})