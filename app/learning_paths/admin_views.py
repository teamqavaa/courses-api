from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import LearningPath, PathOutcome, PathPrerequisite
from .serializers import (
    PathOutcomeWriteSerializer,
    PathPrerequisiteWriteSerializer,
)


def _get_path(slug):
    return get_object_or_404(LearningPath, slug=slug)


# ---------------------------------------------------------------------------
# Path Outcomes
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def admin_path_outcomes(request, path_slug):
    path = _get_path(path_slug)

    if request.method == "POST":
        serializer = PathOutcomeWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        outcome = serializer.save(path=path)
        return Response(PathOutcomeWriteSerializer(outcome).data, status=status.HTTP_201_CREATED)

    outcomes = PathOutcome.objects.filter(path=path)
    serializer = PathOutcomeWriteSerializer(outcomes, many=True)
    return Response(serializer.data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdminUser])
def admin_path_outcome(request, path_slug, pk):
    outcome = get_object_or_404(PathOutcome, pk=pk, path__slug=path_slug)

    if request.method == "GET":
        return Response(PathOutcomeWriteSerializer(outcome).data)

    if request.method == "DELETE":
        PathOutcome.objects.filter(pk=pk, path__slug=path_slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PathOutcomeWriteSerializer(outcome, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(PathOutcomeWriteSerializer(outcome).data)


# ---------------------------------------------------------------------------
# Path Prerequisites
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def admin_path_prerequisites(request, path_slug):
    path = _get_path(path_slug)

    if request.method == "POST":
        serializer = PathPrerequisiteWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        prerequisite = serializer.save(path=path)
        return Response(PathPrerequisiteWriteSerializer(prerequisite).data, status=status.HTTP_201_CREATED)

    prerequisites = PathPrerequisite.objects.filter(path=path)
    serializer = PathPrerequisiteWriteSerializer(prerequisites, many=True)
    return Response(serializer.data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdminUser])
def admin_path_prerequisite(request, path_slug, pk):
    prerequisite = get_object_or_404(PathPrerequisite, pk=pk, path__slug=path_slug)

    if request.method == "GET":
        return Response(PathPrerequisiteWriteSerializer(prerequisite).data)

    if request.method == "DELETE":
        PathPrerequisite.objects.filter(pk=pk, path__slug=path_slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PathPrerequisiteWriteSerializer(prerequisite, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(PathPrerequisiteWriteSerializer(prerequisite).data)
