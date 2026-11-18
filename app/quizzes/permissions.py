"""
Droits sur les quiz (mêmes règles que les cours, core/permissions.py) :
- gérer un quiz : admin, son auteur (instructeur), ou l'instructeur propriétaire du cours de la leçon liée ;
- passer un quiz : inscrit (non suspendu) au cours de la leçon liée, ou toute personne qui peut le gérer (aperçu).
Un quiz rattaché à aucune leçon n'est accessible qu'à ceux qui peuvent le gérer.
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied

from core.permissions import can_edit_course, course_of
from enrollments.models import Enrollment


def lesson_of(quiz):
    """Leçon liée au quiz (Lesson.quiz, OneToOne), ou None."""
    try:
        return quiz.lesson
    except ObjectDoesNotExist:
        return None


def can_manage_quizzes(user):
    return bool(user and user.is_authenticated and getattr(user, 'is_instructor', False))


def can_edit_quiz(user, quiz):
    if not can_manage_quizzes(user):
        return False
    if getattr(user, 'is_admin', False):
        return True
    if quiz.created_by and quiz.created_by == str(user.id):
        return True
    lesson = lesson_of(quiz)
    return lesson is not None and can_edit_course(user, course_of(lesson))


def ensure_can_edit_quiz(user, quiz):
    if not can_edit_quiz(user, quiz):
        raise PermissionDenied("Vous ne pouvez modifier que vos propres quiz.")


def can_take_quiz(user, quiz):
    if not (user and user.is_authenticated):
        return False
    if can_edit_quiz(user, quiz):
        return True
    lesson = lesson_of(quiz)
    if lesson is None:
        return False
    return Enrollment.objects.filter(
        user_id=str(user.id), course=course_of(lesson),
    ).exclude(status='suspended').exists()


def ensure_can_take_quiz(user, quiz):
    if not can_take_quiz(user, quiz):
        raise PermissionDenied("Inscrivez-vous au cours pour passer ce quiz.")
