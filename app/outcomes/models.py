# app/courses/models/outcome.py
import uuid
from django.db import models


class CourseOutcome(models.Model):
    """
    Modèle représentant un objectif pédagogique / acquis d'apprentissage (Course Outcome).
    Il décrit les compétences, savoir-faire ou connaissances que l'étudiant
    acquiert après avoir suivi le cours.
    """

    class OutcomeCategory(models.TextChoices):
        SKILL = 'SKILL', 'Compétence pratique'
        KNOWLEDGE = 'KNOWLEDGE', 'Connaissance théorique'
        TOOL = 'TOOL', 'Maitrise d\'outil / logiciel'
        CERTIFICATION = 'CERTIFICATION', 'Préparation certification'
        OTHER = 'OTHER', 'Autre'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='outcomes',
        verbose_name="Cours associé"
    )
    description = models.TextField(
        verbose_name="Description de l'objectif",
        help_text="Ex: 'Construire une API REST sécurisée avec Django REST Framework'"
    )
    category = models.CharField(
        max_length=20,
        choices=OutcomeCategory.choices,
        default=OutcomeCategory.SKILL,
        verbose_name="Catégorie d'apprentissage"
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Icône FontAwesome / Lucide",
        help_text="Nom de l'icône à afficher côté Frontend (ex: 'check-circle', 'code', 'database')"
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name="Ordre d'affichage",
        help_text="Position dans la liste des objectifs du cours (1, 2, 3...)"
    )
    is_highlighted = models.BooleanField(
        default=False,
        verbose_name="Mettre en avant",
        help_text="Afficher cet objectif en priorité ou sous forme de badge principal"
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Est visible",
        help_text="Permet de masquer temporairement un objectif"
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
        verbose_name = "Objectif du cours"
        verbose_name_plural = "Objectifs du cours"
        ordering = ['order', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'order'],
                name='unique_outcome_order_per_course'
            )
        ]

    def __str__(self):
        return f"[{self.course.title}] Outcome {self.order}: {self.description[:50]}"
