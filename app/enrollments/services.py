# app/enrollments/services.py
"""Calcul de la progression d'un utilisateur sur les cours auxquels il est inscrit."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from lessons.models import Lesson
from .models import Enrollment, LessonProgress


def course_lessons(course):
    """Leçons publiées d'un cours (modules publiés), dans l'ordre du programme."""
    return Lesson.objects.filter(
        module__course=course,
        module__is_published=True,
        is_published=True,
    ).order_by('module__order', 'order')


def recompute_progress(enrollment):
    """Met à jour Enrollment.progress_percentage = leçons terminées / leçons publiées."""
    total = course_lessons(enrollment.course).count()
    completed = enrollment.lesson_progress.filter(
        is_completed=True, lesson__in=course_lessons(enrollment.course)
    ).count()
    percentage = Decimal(completed * 100) / Decimal(total) if total else Decimal('0')
    enrollment.progress_percentage = percentage.quantize(Decimal('0.01'))
    # last_accessed_at (auto_now) est mis à jour par ce save
    enrollment.save(update_fields=['progress_percentage', 'last_accessed_at'])
    return enrollment


def record_lesson_progress(enrollment, lesson, position_seconds=None, completed=False):
    """Enregistre la position de lecture et/ou la fin d'une leçon, puis recalcule la progression."""
    progress, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    if position_seconds is not None:
        progress.position_seconds = position_seconds
    if completed and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
    progress.save()
    recompute_progress(enrollment)
    return progress


def learning_stats(user_id, days=7):
    """
    Statistiques du dashboard : totaux et activité quotidienne sur les `days` derniers jours
    (leçons terminées et minutes de cours correspondantes).
    """
    enrollments = Enrollment.objects.filter(user_id=user_id).exclude(status='suspended')
    count = enrollments.count()
    completed_courses = enrollments.filter(progress_percentage__gte=100).count()
    average = enrollments.aggregate(avg=Avg('progress_percentage'))['avg'] or Decimal('0')

    done = LessonProgress.objects.filter(enrollment__in=enrollments, is_completed=True)

    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    per_day = {
        row['day']: row
        for row in done.filter(completed_at__date__gte=start)
        .annotate(day=TruncDate('completed_at'))
        .values('day')
        .annotate(lessons=Count('id'), minutes=Sum('lesson__duration_in_minutes'))
        .order_by()
    }

    activity = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        activity.append({
            'date': day.isoformat(),
            'lessons_completed': per_day.get(day, {}).get('lessons', 0),
            'minutes': per_day.get(day, {}).get('minutes') or 0,
        })

    return {
        'enrolled_courses': count,
        'completed_courses': completed_courses,
        'in_progress_courses': enrollments.filter(progress_percentage__gt=0, progress_percentage__lt=100).count(),
        'completed_lessons': done.count(),
        'learning_minutes': done.aggregate(total=Sum('lesson__duration_in_minutes'))['total'] or 0,
        'average_progress': float(round(average, 2)),
        'activity': activity,
    }
