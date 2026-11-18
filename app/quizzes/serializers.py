"""
Deux familles de serializers :
- étudiant (Quiz/Question/Choice « Public », QuizAttempt) : jamais is_correct, tests, explication ni réponses
  acceptées avant la correction ; le détail de la correction n'apparaît qu'une fois la tentative soumise ;
- gestion (« Manage ») : tout le contenu, écriture imbriquée des questions et des choix.
"""
import random

from django.db import transaction
from rest_framework import serializers

from .models import Choice, Question, Quiz, QuizAttempt
from .permissions import lesson_of
from .services import MAX_CODE_TESTS, attempt_deadline

CHOICE_TYPES = {Question.Type.SINGLE, Question.Type.MULTIPLE, Question.Type.TRUE_FALSE}


def _shuffled(items, seed):
    items = list(items)
    random.Random(seed).shuffle(items)
    return items


def _lesson_info(quiz):
    lesson = lesson_of(quiz)
    if lesson is None:
        return None
    return {'id': str(lesson.id), 'title': lesson.title, 'course_slug': lesson.module.course.slug}


# ---------------------------------------------------------------------------
# Étudiant
# ---------------------------------------------------------------------------

class ChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text']


class QuestionPublicSerializer(serializers.ModelSerializer):
    choices = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'type', 'statement', 'points', 'order', 'language', 'starter_code', 'choices']

    def get_choices(self, obj) -> list[dict]:
        # Réponse courte : les choix sont les réponses acceptées, jamais envoyées
        if obj.type not in CHOICE_TYPES:
            return []
        choices = obj.choices.all()
        seed = self.context.get('shuffle_seed')
        if seed is not None:
            choices = _shuffled(choices, f'{seed}:{obj.id}')
        return ChoicePublicSerializer(choices, many=True).data


class QuizAttemptSerializer(serializers.ModelSerializer):
    deadline = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'started_at', 'deadline', 'submitted_at', 'score', 'passed', 'answers', 'details']

    def get_deadline(self, obj) -> str | None:
        deadline = attempt_deadline(obj)
        return deadline.isoformat() if deadline else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Avant la soumission : ni score, ni correction
        if instance.submitted_at is None:
            for field in ('score', 'passed', 'answers', 'details'):
                data.pop(field, None)
        return data


class QuizPublicSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    lesson = serializers.SerializerMethodField()
    my_attempts = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'pass_score', 'max_attempts', 'time_limit_min',
            'question_count', 'total_points', 'lesson', 'questions', 'my_attempts',
        ]

    def get_questions(self, obj) -> list[dict]:
        questions = obj.questions.prefetch_related('choices').all()
        seed = self.context.get('shuffle_seed') if obj.shuffle else None
        if seed is not None:
            questions = _shuffled(questions, seed)
        context = {**self.context, 'shuffle_seed': seed}
        return QuestionPublicSerializer(questions, many=True, context=context).data

    def get_question_count(self, obj) -> int:
        return obj.questions.count()

    def get_total_points(self, obj) -> int:
        return obj.total_points

    def get_lesson(self, obj) -> dict | None:
        return _lesson_info(obj)

    def get_my_attempts(self, obj) -> dict:
        user_id = self.context.get('user_id')
        attempts = list(obj.attempts.filter(user_id=user_id)) if user_id else []
        submitted = [attempt for attempt in attempts if attempt.submitted_at]
        in_progress = next((attempt for attempt in attempts if attempt.submitted_at is None), None)
        best = max((attempt.score for attempt in submitted), default=None)
        return {
            'count': len(attempts),
            'remaining': None if obj.max_attempts is None else max(obj.max_attempts - len(attempts), 0),
            'best_score': float(best) if best is not None else None,
            'passed': any(attempt.passed for attempt in submitted),
            'in_progress': QuizAttemptSerializer(in_progress).data if in_progress else None,
            'last_submitted_id': str(submitted[0].id) if submitted else None,
        }


class SubmitAttemptSerializer(serializers.Serializer):
    answers = serializers.DictField(
        help_text="{<question_id>: id de choix | [ids] | texte | code}", allow_empty=True,
    )


# ---------------------------------------------------------------------------
# Gestion (instructeurs, admins)
# ---------------------------------------------------------------------------

class ChoiceManageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct', 'order']


class QuestionManageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    choices = ChoiceManageSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = [
            'id', 'type', 'statement', 'points', 'order', 'explanation',
            'language', 'starter_code', 'tests', 'choices',
        ]

    def validate(self, attrs):
        kind = attrs.get('type', Question.Type.SINGLE)
        choices = attrs.get('choices', [])
        correct = [choice for choice in choices if choice.get('is_correct')]
        if kind in (Question.Type.SINGLE, Question.Type.TRUE_FALSE):
            if len(choices) < 2 or len(correct) != 1:
                raise serializers.ValidationError({'choices': "Au moins 2 choix, dont exactement 1 correct."})
        elif kind == Question.Type.MULTIPLE:
            if len(choices) < 2 or not correct:
                raise serializers.ValidationError({'choices': "Au moins 2 choix, dont au moins 1 correct."})
        elif kind == Question.Type.SHORT:
            if not correct:
                raise serializers.ValidationError({'choices': "Indiquez au moins une réponse acceptée (is_correct)."})
        elif kind == Question.Type.CODE:
            if not attrs.get('language'):
                raise serializers.ValidationError({'language': "Langage requis pour une question de code."})
            tests = attrs.get('tests')
            valid = isinstance(tests, list) and all(
                isinstance(test, dict) and 'expected' in test for test in tests or []
            )
            if not valid or not 1 <= len(tests) <= MAX_CODE_TESTS:
                raise serializers.ValidationError(
                    {'tests': f'De 1 à {MAX_CODE_TESTS} tests [{{"stdin": "...", "expected": "..."}}].'}
                )
        return attrs


class QuizManageSerializer(serializers.ModelSerializer):
    """
    Écriture imbriquée (comme les étapes d'un lab) : `questions` (facultatif) remplace les questions du
    quiz — `id` connu = mise à jour, sans `id` = création, absente = supprimée ; idem pour `choices`.
    """
    questions = QuestionManageSerializer(many=True, required=False)
    lesson = serializers.SerializerMethodField()
    attempts_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'pass_score', 'max_attempts', 'time_limit_min', 'shuffle',
            'created_by', 'created_at', 'updated_at', 'lesson', 'attempts_count', 'questions',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_lesson(self, obj) -> dict | None:
        return _lesson_info(obj)

    def get_attempts_count(self, obj) -> int:
        return obj.attempts.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['questions'] = QuestionManageSerializer(
            instance.questions.prefetch_related('choices').all(), many=True,
        ).data
        return data

    @transaction.atomic
    def create(self, validated_data):
        questions = validated_data.pop('questions', None)
        quiz = Quiz.objects.create(**validated_data)
        if questions is not None:
            _replace_questions(quiz, questions)
        return quiz

    @transaction.atomic
    def update(self, instance, validated_data):
        questions = validated_data.pop('questions', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if questions is not None:
            _replace_questions(instance, questions)
        return instance


def _replace_children(queryset, items, create, update_fields):
    """Met à jour les éléments dont l'id existe, crée les autres, supprime les absents."""
    existing = {str(obj.id): obj for obj in queryset}
    kept = []
    for item in items:
        obj = existing.get(str(item.get('id'))) if item.get('id') else None
        values = {field: item[field] for field in update_fields if field in item}
        if obj is None:
            obj = create(**values)
        else:
            for field, value in values.items():
                setattr(obj, field, value)
            obj.save()
        kept.append(str(obj.id))
    queryset.exclude(id__in=kept).delete()


def _replace_questions(quiz, questions):
    fields = ['type', 'statement', 'points', 'order', 'explanation', 'language', 'starter_code', 'tests']
    existing = {str(question.id): question for question in quiz.questions.all()}
    kept = []
    for index, item in enumerate(questions, start=1):
        item.setdefault('order', index)
        question = existing.get(str(item.get('id'))) if item.get('id') else None
        values = {field: item[field] for field in fields if field in item}
        if question is None:
            question = Question.objects.create(quiz=quiz, **values)
        else:
            for field, value in values.items():
                setattr(question, field, value)
            question.save()
        kept.append(str(question.id))
        choices = item.get('choices', [])
        for position, choice in enumerate(choices, start=1):
            choice.setdefault('order', position)
        _replace_children(
            question.choices.all(), choices,
            lambda question=question, **values: Choice.objects.create(question=question, **values),
            ['text', 'is_correct', 'order'],
        )
    quiz.questions.exclude(id__in=kept).delete()
