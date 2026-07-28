# app/courses/models.py
import uuid
from decimal import Decimal
from django.db import models
from django.utils.text import slugify
from categories.models import Category
from tags.models import Tag


class Course(models.Model):
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
        ("all", "All"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    LANGUAGE_CHOICES = [
        ("english", "English"),
        ("french", "French"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    category = models.ForeignKey(
        Category,
        related_name="courses",
        on_delete=models.PROTECT
    )

    instructor_id = models.UUIDField(
        verbose_name="Instructor UUID"
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField()

    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default="english")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="all")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    price = models.DecimalField(max_digits=10, decimal_places=2)

    # CORRECTION : Utilisation de Decimal("0.00") au lieu de 0.00 (float)
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    # Recensement ajouté

    tags = models.ManyToManyField(Tag, related_name='courses', blank=True)

    # --- CHAMPS HYBRIDES TEXTE / FICHIERS ---
    thumbnail = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Local path (e.g., /media/courses/img.png) or external URL (e.g., https://site.com/img.png)"
    )

    promo_video_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="External URL (YouTube, Vimeo, Cloudinary) or local path to video."
    )
    # ----------------------------------------

    average_rating = models.FloatField(default=0.0)
    total_students = models.IntegerField(default=0)
    total_reviews = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Génère automatiquement un slug unique basé sur le titre s'il n'est pas fourni
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
