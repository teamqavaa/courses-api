import uuid
from django.db import models


class Module(models.Model):
    """
    Modèle représentant un Module (Chapitre/Unité d'apprentissage).
    Gère l'organisation pédagogique et le regroupement des leçons.
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
        related_name='modules',
        verbose_name="Cours associé"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre du module"
    )
    slug = models.SlugField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Slug"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description / Objectifs pédagogiques"
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name="Ordre d'affichage",
        help_text="Position du module dans le cours (ex: 1, 2, 3...)"
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Est publié",
        help_text="Permet de masquer un module en cours de rédaction"
    )
    is_free = models.BooleanField(
        default=False,
        verbose_name="Accès gratuit",
        help_text="Si vrai, l'ensemble des leçons du module est accessible gratuitement"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ['order']
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=['course', 'order'],
                name='unique_module_order_per_course'
            )
        ]

    def __str__(self):
        return f"Module {self.order}: {self.title} ({self.course.title})"
