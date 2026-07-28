from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from courses.models import Course

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),         # L'étudiant a accès au cours
        ('completed', 'Terminé'),     # L'étudiant a fini le cours (100% de progression)
        ('suspended', 'Suspendu'),   # Accès coupé (ex: remboursement, litige de paiement)
    ]

    # 1. Les Relations clé
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name="Étudiant"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name="Cours"
    )

    # Référence vers la commande/paiement qui a généré cette inscription.
    # On utilise une chaîne de caractères 'payments.Order' pour éviter les imports circulaires.
    # null=True et blank=True permettent de gérer d'éventuels cours gratuits sans commande.
    order = models.OneToOneField(
        'payments.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_enrollment',
        verbose_name="Commande d'origine"
    )

    # 2. Suivi de l'apprentissage
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
        # Empêche un utilisateur d'avoir deux inscriptions actives/existantes pour le même cours
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course'],
                name='unique_user_course_enrollment'
            )
        ]
        ordering = ['-enrolled_at']
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"

    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.get_status_display()})"
