import uuid
from django.db import models


class Lesson(models.Model):
    """
    Modèle autonome représentant une Leçon.
    Agit comme l'enveloppe pédagogique rattachée à un Module.
    Le contenu vidéo est géré séparément dans la table `Video`.
    """

    class LessonType(models.TextChoices):
        VIDEO = 'VIDEO', 'Vidéo'
        ARTICLE = 'ARTICLE', 'Article / Texte'
        DOCUMENT = 'DOCUMENT', 'Document (PDF, PPT...)'
        QUIZ = 'QUIZ', 'Quiz / Évaluation'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    module = models.ForeignKey(
        'modules.Module',  # Lazy reference vers le modèle Module
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name="Module parent"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre de la leçon"
    )
    slug = models.SlugField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Slug"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description / Résumé de la leçon"
    )
    lesson_type = models.CharField(
        max_length=15,
        choices=LessonType.choices,
        default=LessonType.VIDEO,
        verbose_name="Type de la leçon"
    )

    # --- Métadonnées & Organisation ---
    duration_in_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Durée estimée (minutes)"
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name="Ordre d'affichage",
        help_text="Position de la leçon dans le module (1, 2, 3...)"
    )

    # --- Contrôle d'Accès ---
    is_preview = models.BooleanField(
        default=False,
        verbose_name="Aperçu gratuit",
        help_text="Permet de rendre cette leçon visionnable sans inscription"
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Est publiée",
        help_text="Masque la leçon aux étudiants si décoché"
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
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"
        ordering = ['order']
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=['module', 'order'],
                name='unique_lesson_order_per_module'
            )
        ]

    def __str__(self):
        return f"Leçon {self.order}: {self.title}"


class LabActivity(models.Model):
    """
    An activity within a lesson that links to an external DRL lab.
    `lab_id` is a UUID referencing the Lab in the DRL backend.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='lab_activities',
    )
    lab_id = models.UUIDField(
        help_text="UUID of the Lab in the DRL backend",
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Override title (optional)",
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name="Position within the lesson",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lab Activity"
        verbose_name_plural = "Lab Activities"
        ordering = ['order']
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=['lesson', 'order'],
                name='unique_lab_activity_order_per_lesson',
            ),
        ]

    def __str__(self):
        label = self.title or f"Lab {self.lab_id}"
        return f"LabActivity({self.lesson.title} → {label})"
