"""
Receivers des signaux d'activité (core/signals.py).

- activity_completed : un lab (ou un quiz) réussi marque terminées les leçons qui le référencent,
  dans les cours où l'utilisateur est inscrit (inscriptions non suspendues).
- Nouvelle inscription (post_save created, ou enrollments_created pour le bulk_create du paiement) :
  rattrapage des leçons LAB dont le lab est déjà réussi dans /labs (lab.UserProgress COMPLETED).

La progression passe par services.record_lesson_progress : idempotent (get_or_create, completed_at
conservé) et recalcul de progress_percentage. Les statistiques existantes ne changent pas.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.signals import activity_completed, enrollments_created
from lab.models import UserProgress
from lessons.models import Lesson

from .models import Enrollment
from .services import record_lesson_progress


def _activity_lessons(lab=None, quiz=None):
    """Leçons qui référencent l'activité réussie."""
    if lab is not None:
        return Lesson.objects.filter(lesson_type=Lesson.LessonType.LAB, lab=lab)
    if quiz is not None:
        return Lesson.objects.filter(lesson_type=Lesson.LessonType.QUIZ, quiz=quiz)
    return Lesson.objects.none()


@receiver(activity_completed, dispatch_uid='enrollments_activity_completed')
def complete_activity_lessons(sender, user_id=None, lab=None, quiz=None, score=None, **kwargs):
    if not user_id:
        return
    lessons = list(_activity_lessons(lab=lab, quiz=quiz).select_related('module'))
    if not lessons:
        return
    enrollments = {
        enrollment.course_id: enrollment
        for enrollment in Enrollment.objects.filter(
            user_id=str(user_id), course_id__in={lesson.module.course_id for lesson in lessons},
        ).exclude(status='suspended')
    }
    for lesson in lessons:
        enrollment = enrollments.get(lesson.module.course_id)
        if enrollment is not None:
            record_lesson_progress(enrollment, lesson, completed=True)


def catch_up_enrollment(enrollment):
    """Marque terminées les leçons LAB du cours dont le lab est déjà réussi par l'utilisateur."""
    if enrollment.status == 'suspended':
        return
    completed_labs = UserProgress.objects.filter(
        user_id=str(enrollment.user_id), status=UserProgress.Status.COMPLETED,
    ).values('lab_id')
    lessons = Lesson.objects.filter(
        module__course_id=enrollment.course_id,
        lesson_type=Lesson.LessonType.LAB,
        lab_id__in=completed_labs,
    )
    for lesson in lessons:
        record_lesson_progress(enrollment, lesson, completed=True)


@receiver(post_save, sender=Enrollment, dispatch_uid='enrollments_catch_up_on_create')
def catch_up_on_create(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        catch_up_enrollment(instance)


@receiver(enrollments_created, dispatch_uid='enrollments_catch_up_on_bulk_create')
def catch_up_on_bulk_create(sender, enrollments=(), **kwargs):
    for enrollment in enrollments:
        # Relu en base : selon le SGBD, bulk_create ne renseigne pas toujours la clé primaire
        saved = Enrollment.objects.filter(user_id=enrollment.user_id, course_id=enrollment.course_id).first()
        if saved is not None:
            catch_up_enrollment(saved)
