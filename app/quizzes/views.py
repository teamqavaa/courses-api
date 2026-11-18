"""
Endpoints des quiz (sous /api/, documentés dans Swagger).

Étudiant (inscrit au cours de la leçon liée, ou gestionnaire du quiz en aperçu) :
- GET  quizzes/<id>/                 quiz et questions, sans aucune bonne réponse
- POST quizzes/<id>/attempts/        démarre une tentative (ou renvoie celle en cours), 403 au-delà de max_attempts
- GET  quiz-attempts/<id>/           sa tentative ; correction visible seulement après soumission
- POST quiz-attempts/<id>/submit/    soumission unique, corrigée côté serveur ; réussite -> activity_completed
Gestion (instructeur : ses quiz et ceux de ses cours ; admin : tous) :
- GET/POST quizzes/manage/, GET/PATCH/DELETE quizzes/manage/<id>/
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Quiz, QuizAttempt
from .permissions import can_manage_quizzes, ensure_can_edit_quiz, ensure_can_take_quiz
from .serializers import (
    QuizAttemptSerializer,
    QuizManageSerializer,
    QuizPublicSerializer,
    SubmitAttemptSerializer,
)
from .services import AlreadySubmitted, is_expired, submit_attempt


def _user_id(request):
    return str(request.user.id)


# ---------------------------------------------------------------------------
# Étudiant
# ---------------------------------------------------------------------------

@extend_schema(responses=QuizPublicSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_detail(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    ensure_can_take_quiz(request.user, quiz)
    context = {'user_id': _user_id(request), 'shuffle_seed': f'{_user_id(request)}:{quiz.id}'}
    return Response(QuizPublicSerializer(quiz, context=context).data)


@extend_schema(request=None, responses={200: QuizAttemptSerializer, 201: QuizAttemptSerializer, 403: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_attempt(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    ensure_can_take_quiz(request.user, quiz)
    user_id = _user_id(request)
    attempts = QuizAttempt.objects.filter(quiz=quiz, user_id=user_id)

    # Tentative en cours encore valable : on la reprend (un rechargement ne consomme pas d'essai)
    current = attempts.filter(submitted_at__isnull=True).select_related('quiz').first()
    if current is not None and not is_expired(current):
        return Response(QuizAttemptSerializer(current).data, status=status.HTTP_200_OK)

    if quiz.max_attempts is not None and attempts.count() >= quiz.max_attempts:
        return Response(
            {'detail': "Nombre maximum de tentatives atteint pour ce quiz."},
            status=status.HTTP_403_FORBIDDEN,
        )
    attempt = QuizAttempt.objects.create(quiz=quiz, user_id=user_id)
    return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


def _own_attempt(request, pk):
    # 404 (et non 403) pour la tentative d'un autre : son existence n'est pas révélée
    return get_object_or_404(QuizAttempt.objects.select_related('quiz'), pk=pk, user_id=_user_id(request))


@extend_schema(responses=QuizAttemptSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attempt_detail(request, pk):
    return Response(QuizAttemptSerializer(_own_attempt(request, pk)).data)


@extend_schema(request=SubmitAttemptSerializer, responses={200: QuizAttemptSerializer, 409: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def attempt_submit(request, pk):
    attempt = _own_attempt(request, pk)
    payload = SubmitAttemptSerializer(data=request.data)
    payload.is_valid(raise_exception=True)
    try:
        attempt = submit_attempt(attempt.pk, _user_id(request), payload.validated_data['answers'])
    except AlreadySubmitted:
        return Response({'detail': "Cette tentative a déjà été soumise."}, status=status.HTTP_409_CONFLICT)
    return Response(QuizAttemptSerializer(attempt).data)


# ---------------------------------------------------------------------------
# Gestion
# ---------------------------------------------------------------------------

def _ensure_manager(user):
    if not can_manage_quizzes(user):
        raise PermissionDenied("Réservé aux instructeurs et aux administrateurs.")


def _managed_quizzes(user):
    queryset = Quiz.objects.select_related('lesson__module__course').prefetch_related('questions__choices')
    if getattr(user, 'is_admin', False):
        return queryset
    user_id = str(user.id)
    return queryset.filter(Q(created_by=user_id) | Q(lesson__module__course__user_id=user_id))


@extend_schema(
    methods=['GET'],
    parameters=[OpenApiParameter('search', str, description='Recherche dans le titre')],
    responses=QuizManageSerializer(many=True),
)
@extend_schema(methods=['POST'], request=QuizManageSerializer, responses={201: QuizManageSerializer})
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def quiz_manage_list(request):
    _ensure_manager(request.user)
    if request.method == 'GET':
        quizzes = _managed_quizzes(request.user)
        search = request.query_params.get('search')
        if search:
            quizzes = quizzes.filter(title__icontains=search)
        return Response(QuizManageSerializer(quizzes, many=True).data)

    serializer = QuizManageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    quiz = serializer.save(created_by=_user_id(request))
    return Response(QuizManageSerializer(quiz).data, status=status.HTTP_201_CREATED)


@extend_schema(methods=['GET'], responses=QuizManageSerializer)
@extend_schema(methods=['PATCH'], request=QuizManageSerializer, responses=QuizManageSerializer)
@extend_schema(methods=['DELETE'], responses={204: None, 409: None})
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def quiz_manage_detail(request, pk):
    _ensure_manager(request.user)
    quiz = get_object_or_404(Quiz, pk=pk)
    ensure_can_edit_quiz(request.user, quiz)

    if request.method == 'GET':
        return Response(QuizManageSerializer(quiz).data)

    if request.method == 'DELETE':
        # Comme les labs : un instructeur ne supprime pas un quiz déjà passé par des apprenants
        others = quiz.attempts.exclude(user_id=_user_id(request)).exists()
        if others and not request.user.is_admin:
            return Response(
                {'detail': "Des apprenants ont passé ce quiz : il ne peut pas être supprimé."},
                status=status.HTTP_409_CONFLICT,
            )
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = QuizManageSerializer(quiz, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    return Response(QuizManageSerializer(serializer.save()).data)
