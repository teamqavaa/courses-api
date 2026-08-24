# app/resources/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from resources.models import Resource
from resources.serializers import ResourceDetailSerializer, ResourceCreateUpdateSerializer


class HasSSORole(permissions.BasePermission):
    """Permission basée sur le rôle SSO."""
    ALLOWED_WRITE_ROLES = {'instructor', 'admin', 'staff'}

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        user_role = getattr(request.user, 'role', None)
        return user_role in self.ALLOWED_WRITE_ROLES or getattr(request.user, 'is_staff', False)


class ResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet unifié pour les Ressources de Cours, Modules et Leçons.

    Filtres disponibles :
    - GET /api/resources/?course={course_uuid}
    - GET /api/resources/?module={module_uuid}
    - GET /api/resources/?lesson={lesson_uuid}
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, HasSSORole]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'module', 'lesson', 'resource_type', 'is_published']

    def get_queryset(self):
        user = self.request.user
        queryset = Resource.objects.all()

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
        if self.action in ['list', 'retrieve']:
            return ResourceDetailSerializer
        return ResourceCreateUpdateSerializer
