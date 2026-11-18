"""
Correction des tentatives de quiz, entièrement côté serveur.

Barème par type de question (voir aussi quizzes/models.py) :
- single / true_false : tous les points si le choix envoyé est un choix correct, sinon 0 ;
- multiple : TOUT OU RIEN — tous les points seulement si l'ensemble des choix envoyés est exactement
  l'ensemble des choix corrects (aucun oubli, aucun choix faux), sinon 0 ;
- short : tous les points si le texte, sans casse ni espaces superflus, égale une réponse acceptée
  (Choice is_correct) ;
- code : points × tests réussis / tests totaux (arrondi à 2 décimales). Un test est réussi si la sortie
  standard, sans espaces de fin, égale `expected`. Piston est appelé directement (lab.piston.run_code).
Score (%) = points obtenus / points totaux × 100 ; réussi si score >= pass_score.
"""
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from core.signals import activity_completed
from lab.piston import PistonError, run_code

from .models import Question, Quiz, QuizAttempt

# Tolérance réseau après la fin du temps imparti
SUBMIT_GRACE = timedelta(seconds=30)
# Nombre maximum de tests exécutés par question de code
MAX_CODE_TESTS = 10
# Taille maximale du code soumis pour une question
MAX_CODE_LENGTH = 20000

TWO_PLACES = Decimal('0.01')


def attempt_deadline(attempt):
    """Date limite de soumission, ou None sans limite de temps."""
    if not attempt.quiz.time_limit_min:
        return None
    return attempt.started_at + timedelta(minutes=attempt.quiz.time_limit_min)


def is_expired(attempt, now=None):
    deadline = attempt_deadline(attempt)
    return deadline is not None and (now or timezone.now()) > deadline + SUBMIT_GRACE


def _normalize(text):
    return ' '.join(str(text or '').split()).casefold()


def _correct_ids(question):
    return {str(choice.id) for choice in question.choices.all() if choice.is_correct}


def _grade_choices(question, answer):
    correct = _correct_ids(question)
    if question.type == Question.Type.MULTIPLE:
        given = {str(item) for item in answer} if isinstance(answer, list) else set()
        ok = bool(correct) and given == correct
    else:
        ok = isinstance(answer, str) and answer in correct
    return {'earned': question.points if ok else 0, 'correct': ok, 'correct_choice_ids': sorted(correct)}


def _grade_short(question, answer):
    accepted = [choice.text for choice in question.choices.all() if choice.is_correct]
    ok = isinstance(answer, str) and _normalize(answer) in {_normalize(text) for text in accepted}
    return {'earned': question.points if ok else 0, 'correct': ok, 'accepted_answers': accepted}


def _grade_code(question, answer):
    tests = list(question.tests or [])[:MAX_CODE_TESTS]
    code = answer if isinstance(answer, str) else ''
    results = []
    if code.strip() and len(code) <= MAX_CODE_LENGTH:
        for test in tests:
            stdin, expected = str(test.get('stdin', '')), str(test.get('expected', ''))
            try:
                output = run_code(question.language, code, stdin)
                actual = output['stdout'].rstrip()
                results.append({
                    'stdin': stdin, 'expected': expected, 'actual': actual,
                    'stderr': output['stderr'][:2000], 'passed': actual == expected.rstrip(),
                })
            except PistonError as error:
                results.append({'stdin': stdin, 'expected': expected, 'error': str(error), 'passed': False})
    else:
        results = [{'stdin': str(t.get('stdin', '')), 'expected': str(t.get('expected', '')), 'passed': False}
                   for t in tests]

    passed = sum(1 for result in results if result['passed'])
    earned = (Decimal(question.points) * passed / len(tests)).quantize(TWO_PLACES) if tests else Decimal('0')
    return {'earned': float(earned), 'correct': bool(tests) and passed == len(tests), 'tests': results}


def grade_question(question, answer):
    if question.type == Question.Type.SHORT:
        result = _grade_short(question, answer)
    elif question.type == Question.Type.CODE:
        result = _grade_code(question, answer)
    else:
        result = _grade_choices(question, answer)
    return {
        'question_id': str(question.id),
        'type': question.type,
        'points': question.points,
        'answer': answer,
        'explanation': question.explanation,
        **result,
    }


def grade(quiz, answers):
    """Retourne (score %, détails par question)."""
    answers = answers if isinstance(answers, dict) else {}
    questions = quiz.questions.prefetch_related('choices').all()
    details = [grade_question(question, answers.get(str(question.id))) for question in questions]
    total = sum(question.points for question in questions)
    earned = sum(Decimal(str(item['earned'])) for item in details)
    score = (earned * 100 / total).quantize(TWO_PLACES, ROUND_HALF_UP) if total else Decimal('0.00')
    return score, details


class AlreadySubmitted(Exception):
    pass


def submit_attempt(attempt_id, user_id, answers):
    """
    Corrige et clôt une tentative (une seule soumission). Une soumission hors délai est enregistrée
    avec un score de 0. Si le quiz est réussi, émet activity_completed (après la transaction).
    """
    with transaction.atomic():
        attempt = QuizAttempt.objects.select_for_update().select_related('quiz').get(pk=attempt_id, user_id=user_id)
        if attempt.submitted_at is not None:
            raise AlreadySubmitted()
        now = timezone.now()
        quiz = attempt.quiz
        if is_expired(attempt, now):
            score, details = Decimal('0.00'), [{'expired': True}]
        else:
            score, details = grade(quiz, answers)
        attempt.answers = answers if isinstance(answers, dict) else {}
        attempt.details = details
        attempt.score = score
        attempt.passed = score >= quiz.pass_score and not is_expired(attempt, now)
        attempt.submitted_at = now
        attempt.save(update_fields=['answers', 'details', 'score', 'passed', 'submitted_at'])

    if attempt.passed:
        activity_completed.send(sender=Quiz, user_id=user_id, quiz=quiz, score=float(score))
    return attempt
