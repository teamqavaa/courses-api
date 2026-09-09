from rest_framework import serializers

from courses.models import Course

from .models import LearningPath, PathOutcome, PathPrerequisite


class PathOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathOutcome
        fields = ['id', 'order', 'content']


class PathOutcomeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathOutcome
        fields = ['id', 'order', 'content']
        read_only_fields = ['id']


class PathPrerequisiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathPrerequisite
        fields = ['id', 'order', 'content']


class PathPrerequisiteWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathPrerequisite
        fields = ['id', 'order', 'content']
        read_only_fields = ['id']


class LearningPathSerializer(serializers.ModelSerializer):
    # The dashboard keys every path URL and recommendation on the slug; `id`
    # is exposed as the slug so `summary.id` works with lookup_field='slug'.
    id = serializers.CharField(source='slug', read_only=True)

    # Computed count of attached published courses; not editable through the API.
    course_count = serializers.SerializerMethodField()

    # Course slugs (matches the courses API `id` = slug convention) so the
    # admin console and dashboards share one identity for a course.
    courses = serializers.SlugRelatedField(
        slug_field='slug',
        many=True,
        required=False,
        queryset=Course.objects.all(),
    )

    class Meta:
        model = LearningPath
        fields = [
            'id',
            'kind',
            'title',
            'slug',
            'description',
            'icon',
            'duration_weeks',
            'pace',
            'includes_certificate',
            'order',
            'is_active',
            'courses',
            'course_count',
            'created_at',
            'updated_at',
        ]
        # slug is auto-generated in save(); timestamps are set automatically by Django.
        read_only_fields = ['id', 'course_count', 'created_at', 'updated_at']

    def get_course_count(self, obj):
        return obj.courses.filter(status='published').count()


# Payload for the /detail/ action: path + bullets + courses in one response so
# the frontend detail page needs a single request.
class LearningPathDetailSerializer(LearningPathSerializer):
    outcomes = PathOutcomeSerializer(many=True, read_only=True)
    prerequisites = PathPrerequisiteSerializer(many=True, read_only=True)
    courses = serializers.SerializerMethodField()

    class Meta(LearningPathSerializer.Meta):
        fields = LearningPathSerializer.Meta.fields + [
            'outcomes',
            'prerequisites',
            'courses',
        ]

    def get_courses(self, obj):
        from courses.serializers import CourseListItemSerializer

        # The detail view always prefetches published courses (with their nested
        # relations), so .all() reads the prefetch cache instead of re-querying.
        return CourseListItemSerializer(obj.courses.all(), many=True).data