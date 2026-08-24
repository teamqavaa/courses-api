# app/resources/models.py
import uuid
import os
from django.db import models
from django.core.exceptions import ValidationError


def resource_upload_path(instance, filename):
    """
    Génère un chemin de stockage dynamique propre dans le Bucket/Storage S3.
    Ex: resources/courses/{course_id}/{filename}
        resources/lessons/{lesson_id}/{filename}
    """
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    clean_filename = f"{name}_{uuid.uuid4().hex[:8]}.{ext}"

    if instance.lesson_id:
        return f"resources/lessons/{instance.lesson_id}/{clean_filename}"
    elif instance.module_id:
        return f"resources/modules/{instance.module_id}/{clean_filename}"
    elif instance.course_id:
        return f"resources/courses/{instance.course_id}/{clean_filename}"
    return f"resources/general/{clean_filename}"


class Resource(models.Model):
    """
    Modèle représentant un fichier ou une ressource téléchargeable.
    Peut être lié à un Cours, un Module OU une Leçon.
    """

    class ResourceTypeChoices(models.TextChoices):
        DOCUMENT = 'DOCUMENT', 'Document (PDF, Word, TXT)'
        ARCHIVE = 'ARCHIVE', 'Archive (ZIP, RAR, TAR)'
        CODE = 'CODE', 'Fichier Code / projet (JS, PY, JSON...)'
        AUDIO = 'AUDIO', 'Fichier Audio (MP3, WAV)'
        IMAGE = 'IMAGE', 'Image / Schéma (PNG, JPG, SVG)'
        EXTERNAL_LINK = 'EXTERNAL_LINK', 'Lien externe (GitHub, Notion, Figma)'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )

    # --- Relations optionnelles (Au moins une doit être renseignée) ---
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='resources',
        blank=True,
        null=True,
        verbose_name="Cours associé"
    )
    module = models.ForeignKey(
        'modules.Module',
        on_delete=models.CASCADE,
        related_name='resources',
        blank=True,
        null=True,
        verbose_name="Module associé"
    )
    lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.CASCADE,
        related_name='resources',
        blank=True,
        null=True,
        verbose_name="Leçon associée"
    )

    # --- Informations de la ressource ---
    title = models.CharField(
        max_length=255,
        verbose_name="Titre du fichier / ressource"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description courte"
    )
    resource_type = models.CharField(
        max_length=20,
        choices=ResourceTypeChoices.choices,
        default=ResourceTypeChoices.DOCUMENT,
        verbose_name="Type de ressource"
    )

    # Stockage de fichier physique OU Lien externe
    file = models.FileField(
        upload_to=resource_upload_path,
        blank=True,
        null=True,
        verbose_name="Fichier téléchargeable"
    )
    external_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Lien externe (ex: GitHub, Figma)"
    )
    file_size_bytes = models.BigIntegerField(
        default=0,
        verbose_name="Taille du fichier (en octets)"
    )
    is_preview_allowed = models.BooleanField(
        default=False,
        verbose_name="Accessible en aperçu gratuit"
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Est publiée"
    )

    # --- Traçabilité ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ressource"
        verbose_name_plural = "Ressources"
        ordering = ['-created_at']

    def clean(self):
        """Validation métiers pour garantir l'intégrité de la ressource."""
        # 1. Vérifier qu'au moins une relation existe
        if not any([self.course_id, self.module_id, self.lesson_id]):
            raise ValidationError("Une ressource doit être rattachée à un Cours, un Module ou une Leçon.")

        # 2. Vérifier qu'un fichier OU une URL externe est fourni
        if not self.file and not self.external_url:
            raise ValidationError("Vous devez fournir un fichier téléchargeable ou une URL externe.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.file and hasattr(self.file, 'size'):
            self.file_size_bytes = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        parent = self.lesson or self.module or self.course
        return f"Resource: {self.title} ({parent})"
