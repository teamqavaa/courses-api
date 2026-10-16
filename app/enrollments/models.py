from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from courses.models import Course


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('completed', 'Terminé'),
        ('suspended', 'Suspendu'),
    ]

    # Remplacez la relation ForeignKey par un CharField pour stocker le sub SSO
    user_id = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="ID Utilisateur (sub)"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name="Cours"
    )

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrollments', # Changé de 'triggered_enrollment' à 'enrollments' (au pluriel)
        verbose_name="Commande d'origine"
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'inscription"
    )
    last_accessed_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernier accès"
    )
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        verbose_name="Progression (%)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Statut de l'accès"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'course'],
                name='unique_user_course_enrollment'
            )
        ]
        ordering = ['-enrolled_at']
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"

    def __str__(self):
        return f"Utilisateur {self.user_id} - {self.course.title} ({self.get_status_display()})"


class LessonProgress(models.Model):
    """
    Progression de l'utilisateur sur une leçon d'un cours auquel il est inscrit.
    Sert à calculer Enrollment.progress_percentage et les statistiques du dashboard.
    """
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name="Inscription"
    )
    lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.CASCADE,
        related_name='progress_entries',
        verbose_name="Leçon"
    )
    position_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="Position de lecture (secondes)"
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Leçon terminée"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de fin de la leçon"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['enrollment', 'lesson'],
                name='unique_enrollment_lesson_progress'
            )
        ]
        ordering = ['-updated_at']
        verbose_name = "Progression d'une leçon"
        verbose_name_plural = "Progressions des leçons"

    def __str__(self):
        state = "terminée" if self.is_completed else f"{self.position_seconds}s"
        return f"{self.enrollment} - {self.lesson.title} ({state})"
