from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from courses.serializers import CourseListItemSerializer
from enrollments.models import Enrollment
from learning_paths.models import LearningPath
from learning_paths.serializers import LearningPathSerializer

from .models import CourseProgress
from .serializers import CourseProgressSerializer


PUBLISHED = 'published'


class MyProgressView(APIView):
    """GET /api/my/progress/?path=<slug>&status=<status> - the caller's progress rows."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = CourseProgress.objects.filter(user_id=request.user.id)
        path_slug = request.query_params.get("path")
        if path_slug:
            course_ids = LearningPath.objects.filter(
                slug=path_slug,
            ).values_list("courses__id", flat=True)
            queryset = queryset.filter(course_id__in=course_ids)
        status_param = request.query_params.get("status")
        valid_statuses = CourseProgress.Status.values
        if status_param:
            if status_param not in valid_statuses:
                return Response(
                    {"error": f"Invalid status. Allowed: {', '.join(valid_statuses)}."},
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_param)
        serializer = CourseProgressSerializer(queryset, many=True)
        return Response(serializer.data)


class SingleMyProgressView(APIView):
    """GET /api/my/progress/<slug>/ - one row or a not_started fallback."""

    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(Course, slug=course_id)
        progress = CourseProgress.objects.filter(
            user_id=request.user.id,
            course=course,
        ).first()
        if progress is None:
            return Response({"course_id": course.slug, "status": "not_started", "progress_percent": 0})
        serializer = CourseProgressSerializer(progress)
        return Response(serializer.data)


class MyCourseStatsView(APIView):
    """GET /api/my/course-stats/ - dashboard counters derived from progress rows."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        rows = CourseProgress.objects.filter(user_id=user_id)
        completed_ids = set(
            rows.filter(
                status=CourseProgress.Status.COMPLETED,
            ).values_list("course_id", flat=True)
        )
        courses_in_progress = rows.filter(
            status=CourseProgress.Status.IN_PROGRESS,
        ).count()

        active_courses = LearningPath.objects.annotate(
            has_progress=Exists(
                CourseProgress.objects.filter(
                    user_id=user_id,
                    course__status=PUBLISHED,
                    course__learning_paths=OuterRef("pk"),
                )
            )
        )
        paths_started = 0
        paths_completed = 0
        for path in active_courses.prefetch_related("courses"):
            active_ids = set(
                path.courses.filter(status=PUBLISHED).values_list("id", flat=True)
            )
            # Paths without published courses cannot be completed, so they stay
            # out of both counters.
            if not active_ids:
                continue
            if path.has_progress:
                paths_started += 1
            if active_ids <= completed_ids:
                paths_completed += 1

        return Response(
            {
                "courses_completed": len(completed_ids),
                "paths_completed": paths_completed,
                "paths_started": paths_started,
                "courses_in_progress": courses_in_progress,
            }
        )


class RecommendationView(APIView):
    """GET /api/my/recommendation/ - one featured next step for the dashboard.

    Order: an untouched path (career kind first), else the newest catalog
    course the user has not completed, else empty nulls.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        touched_ids = list(
            CourseProgress.objects.filter(user_id=user_id).values_list(
                "course_id", flat=True
            )
        )
        completed_ids = set(
            CourseProgress.objects.filter(
                user_id=user_id,
                status=CourseProgress.Status.COMPLETED,
            ).values_list("course_id", flat=True)
        )

        for kind in ("career", "skill"):
            # Zero-course paths can never be started or completed, so they
            # must not soak up the recommendation slot.
            path = (
                LearningPath.objects.filter(
                    is_active=True,
                    kind=kind,
                    courses__status=PUBLISHED,
                )
                .exclude(courses__id__in=touched_ids)
                .distinct()
                .order_by("order", "id")
                .first()
            )
            if path:
                return Response(
                    {
                        "kind": kind,
                        "reason": "Start something new",
                        "path": LearningPathSerializer(path).data,
                        "course": None,
                    }
                )

        course = (
            Course.objects.filter(status=PUBLISHED)
            .exclude(id__in=completed_ids)
            .order_by("-created_at", "-id")
            .first()
        )
        if course:
            return Response(
                {
                    "kind": "course",
                    "reason": "Fresh in the catalog",
                    "path": None,
                    "course": CourseListItemSerializer(course).data,
                }
            )

        return Response({"kind": None, "reason": "", "path": None, "course": None})


class StartCourseView(APIView):
    """POST /api/my/progress/<slug>/start/ - marks a course in progress."""

    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, slug=course_id, status=PUBLISHED)

        if not Enrollment.objects.filter(user_id=str(request.user.id), course=course, status='active').exists():
            return Response(
                {"detail": "You must purchase this course to enroll."},
                status=http_status.HTTP_403_FORBIDDEN
            )

        progress = CourseProgress.objects.filter(user_id=request.user.id, course=course).first()
        if progress is None:
            progress = CourseProgress.objects.create(user_id=request.user.id, course=course)
        elif progress.status == CourseProgress.Status.COMPLETED:
            serializer = CourseProgressSerializer(progress)
            return Response(serializer.data)
        progress.status = CourseProgress.Status.IN_PROGRESS
        progress.completed_at = None
        progress.save()
        serializer = CourseProgressSerializer(progress)
        return Response(serializer.data)


class CompleteCourseView(APIView):
    """POST /api/my/progress/<slug>/complete/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, slug=course_id, status=PUBLISHED)
        progress, _ = CourseProgress.objects.update_or_create(
            user_id=request.user.id,
            course=course,
            defaults={
                "status": CourseProgress.Status.COMPLETED,
                "progress_percent": 100,
                "completed_at": timezone.now(),
            },
        )
        serializer = CourseProgressSerializer(progress)
        return Response(serializer.data)


class UncompleteCourseView(APIView):
    """POST /api/my/progress/<slug>/uncomplete/ - reopens a completed course."""

    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, slug=course_id)
        try:
            progress = CourseProgress.objects.get(user_id=request.user.id, course=course)
        except CourseProgress.DoesNotExist:
            return Response(
                {"error": "No progress record for this course."},
                status=http_status.HTTP_404_NOT_FOUND,
            )
        progress.status = CourseProgress.Status.IN_PROGRESS
        # Keep the bar below 100 so it reads as in-progress again.
        progress.progress_percent = min(progress.progress_percent, 99)
        progress.completed_at = None
        progress.save()
        serializer = CourseProgressSerializer(progress)
        return Response(serializer.data)