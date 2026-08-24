# app/learning_points/models.py
import uuid
from django.db import models


class CourseLearningPoint(models.Model):
    """
    Modèle représentant un point d'apprentissage clé du cours (Key Takeaway).
    Il spécifie une notion précise ou un concept clé abordé dans le cours.
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
        related_name='learning_points',
        verbose_name="Cours associé"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre du point d'apprentissage",
        help_text="Ex: 'Architecture MVC et séparation des responsabilités'"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description détaillée",
        help_text="Explication plus détaillée de ce que couvre ce point."
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Icône FontAwesome / Lucide",
        help_text="Nom de l'icône UI (ex: 'lightbulb', 'book-open', 'cpu', 'layers')"
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
        verbose_name = "Point d'apprentissage du cours"
        verbose_name_plural = "Points d'apprentissage du cours"
        ordering = ['order', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'order'],
                name='unique_learning_point_order_per_course'
            )
        ]

    def __str__(self):
        return f"[{self.course.title}] Learning Point {self.order}: {self.title}"
