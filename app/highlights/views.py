# app/highlights/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import CourseHighlight
from .serializers import (
    CourseHighlightDetailSerializer,
    CourseHighlightCreateUpdateSerializer
)


class HasSSORole(permissions.BasePermission):
    """
    Permission SSO :
    - Lecture : Ouverte à tous.
    - Écriture : Réservée aux 'instructor', 'admin' ou 'staff'.
    """
    ALLOWED_WRITE_ROLES = {'instructor', 'admin', 'staff'}

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, 'role', None)
        return user_role in self.ALLOWED_WRITE_ROLES or getattr(request.user, 'is_staff', False)


class CourseHighlightViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des Points Forts du Cours (CourseHighlight)."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, HasSSORole]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'is_published']

    def get_queryset(self):
        user = self.request.user
        queryset = CourseHighlight.objects.select_related('course').all()

        if user.is_authenticated:
            user_role = getattr(user, 'role', None)
            is_admin_or_instructor = (
                user_role in {'instructor', 'admin', 'staff'} or
                getattr(user, 'is_staff', False)
            )
            if is_admin_or_instructor:
                return queryset

        return queryset.filter(is_published=True)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'by_course']:
            return CourseHighlightDetailSerializer
        return CourseHighlightCreateUpdateSerializer

    @action(detail=False, methods=['get'], url_path='by-course/(?P<course_id>[^/.]+)')
    def by_course(self, request, course_id=None):
        """GET /api/course-highlights/by-course/{course_uuid}/"""
        highlights = self.get_queryset().filter(course_id=course_id).order_by('order')
        serializer = CourseHighlightDetailSerializer(highlights, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
