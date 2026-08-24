# app/highlights/models.py
import uuid
from django.db import models


class CourseHighlight(models.Model):
    """
    Modèle représentant un point fort / avantage clé du cours (Course Highlight).
    Exemples : 'Accès illimité 24/7', 'Projet pratique inclus', 'Accompagnement 1-on-1'.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='highlights',
        verbose_name="Cours associé"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre du point fort",
        help_text="Ex: 'Certificat de réussite'"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description détaillée",
        help_text="Ex: 'Délivré automatiquement à la fin de toutes les leçons'"
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Icône FontAwesome / Lucide",
        help_text="Nom de l'icône UI (ex: 'award', 'clock', 'infinity', 'shield-check')"
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name="Ordre d'affichage"
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Est visible"
    )

    # --- Traçabilité ---
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )

    class Meta:
        verbose_name = "Point fort du cours"
        verbose_name_plural = "Points forts du cours"
        ordering = ['order', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'order'],
                name='unique_highlight_order_per_course'
            )
        ]

    def __str__(self):
        return f"[{self.course.title}] Highlight {self.order}: {self.title}"
