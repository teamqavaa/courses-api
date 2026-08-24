# app/videos/models.py
import uuid
from django.db import models


class Video(models.Model):
    """
    Modèle représentant la vidéo rattachée à une Leçon.
    Séparé du modèle Lesson pour isoler la gestion technique des flux et de l'hébergement.
    """

    class ProviderChoices(models.TextChoices):
        VIMEO = 'VIMEO', 'Vimeo'
        CLOUDFLARE = 'CLOUDFLARE', 'Cloudflare Stream'
        YOUTUBE = 'YOUTUBE', 'YouTube'
        BUNNY = 'BUNNY', 'Bunny CDN'
        S3_HLS = 'S3_HLS', 'AWS S3 / HLS (.m3u8)'
        OTHER = 'OTHER', 'Autre / URL direct'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    lesson = models.OneToOneField(
        'lessons.Lesson',
        on_delete=models.CASCADE,
        related_name='video',
        verbose_name="Leçon associée"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre de la vidéo"
    )
    provider = models.CharField(
        max_length=20,
        choices=ProviderChoices.choices,
        default=ProviderChoices.YOUTUBE,
        verbose_name="Fournisseur d'hébergement"
    )
    video_url = models.URLField(
        max_length=500,
        verbose_name="URL de la vidéo / Flux HLS",
        help_text="URL principale de lecture ou manifest .m3u8"
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID Externe / Cloudflare UID",
        help_text="ID de la vidéo chez le fournisseur (ex: Cloudflare UID ou Vimeo ID)"
    )
    thumbnail_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL de la miniature (Thumbnail)"
    )
    duration_in_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="Durée (en secondes)",
        help_text="Durée exacte de la vidéo"
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
        verbose_name = "Vidéo"
        verbose_name_plural = "Vidéos"

    def __str__(self):
        return f"Vidéo: {self.title} (Leçon: {self.lesson.title})"
