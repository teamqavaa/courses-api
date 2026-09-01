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

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_enrollment',
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
