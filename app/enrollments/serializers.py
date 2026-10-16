# app/enrollments/serializers.py
from rest_framework import serializers
from courses.models import Course
from courses.serializers import CourseSerializer
from .models import Enrollment, LessonProgress
from .services import course_lessons

class EnrollmentSerializer(serializers.ModelSerializer):
    # Permet d'intégrer tous les détails du cours dans l'inscription (GET)
    course_details = CourseSerializer(source='course', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'course',          # Utilisé pour spécifier le cours à l'écriture (si besoin)
            'course_details',   # Utilisé pour afficher les détails du cours en lecture
            'enrolled_at',
            'last_accessed_at',
            'progress_percentage',
            'status'
        ]
        read_only_fields = [
            'id',
            'enrolled_at',
            'last_accessed_at',
            'progress_percentage',
            'status'
        ]


class EnrollmentCourseSerializer(serializers.ModelSerializer):
    """Résumé d'un cours pour le dashboard (sans le programme complet)."""
    category = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'slug', 'title', 'subtitle', 'description', 'thumbnail', 'level',
            'language', 'average_rating', 'user_email', 'category',
        ]
        read_only_fields = fields

    def get_category(self, obj) -> dict:
        return {'name': obj.category.name, 'slug': obj.category.slug}


class DashboardEnrollmentSerializer(serializers.ModelSerializer):
    """
    Inscription de l'utilisateur connecté avec sa progression de lecture
    (GET /api/enrollments/ et /api/enrollments/<slug>/).
    """
    course = EnrollmentCourseSerializer(read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    total_lessons = serializers.SerializerMethodField()
    completed_lessons = serializers.SerializerMethodField()
    total_duration_minutes = serializers.SerializerMethodField()
    completed_lesson_ids = serializers.SerializerMethodField()
    last_lesson = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'status', 'enrolled_at', 'last_accessed_at', 'progress_percentage',
            'total_lessons', 'completed_lessons', 'total_duration_minutes',
            'completed_lesson_ids', 'last_lesson', 'course',
        ]
        read_only_fields = fields

    def _lessons(self, obj):
        if not hasattr(obj, '_cached_lessons'):
            obj._cached_lessons = list(course_lessons(obj.course))
        return obj._cached_lessons

    def get_total_lessons(self, obj) -> int:
        return len(self._lessons(obj))

    def get_total_duration_minutes(self, obj) -> int:
        return sum(lesson.duration_in_minutes for lesson in self._lessons(obj))

    def get_completed_lesson_ids(self, obj) -> list[str]:
        published = {lesson.id for lesson in self._lessons(obj)}
        return [
            str(p.lesson_id) for p in obj.lesson_progress.all()
            if p.is_completed and p.lesson_id in published
        ]

    def get_completed_lessons(self, obj) -> int:
        return len(self.get_completed_lesson_ids(obj))

    def get_last_lesson(self, obj) -> dict | None:
        """Dernière leçon consultée (pour reprendre la lecture), sinon la première du cours."""
        latest = max(obj.lesson_progress.all(), key=lambda p: p.updated_at, default=None)
        if latest:
            lesson, position = latest.lesson, latest.position_seconds
        else:
            lessons = self._lessons(obj)
            if not lessons:
                return None
            lesson, position = lessons[0], 0
        return {
            'id': str(lesson.id),
            'slug': lesson.slug,
            'title': lesson.title,
            'position_seconds': position,
        }


class LessonProgressInputSerializer(serializers.Serializer):
    """POST /api/enrollments/<slug>/progress/"""
    lesson_id = serializers.UUIDField()
    position_seconds = serializers.IntegerField(min_value=0, required=False)
    completed = serializers.BooleanField(required=False, default=False)


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['lesson', 'position_seconds', 'is_completed', 'completed_at', 'updated_at']
        read_only_fields = fields
