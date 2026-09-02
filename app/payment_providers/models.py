import uuid
from django.db import models


class PaymentProvider(models.Model):
    """
    Modèle représentant un prestataire de paiement.
    Permet de gérer dynamiquement les passerelles actives et leurs configurations.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="UUID Identifier"
    )
    user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Created By User ID",
        help_text="ID SSO de l'administrateur ayant créé ce prestataire"
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Provider Name",
        help_text="Nom affiché au client (ex: Qavaa, Ignite)"
    )
    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Provider Code",
        help_text="Identifiant technique unique du prestataire (ex: QAVAA, IGNITE)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Active ou désactive ce moyen de paiement sur la plateforme"
    )
    logo = models.ImageField(
        upload_to='payment_providers/',
        null=True,
        blank=True,
        verbose_name="Logo",
        help_text="Icône ou logo à afficher sur le checkout frontend"
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Provider Configuration",
        help_text="Clés API ou paramètres spécifiques"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    class Meta:
        verbose_name = "Payment Provider"
        verbose_name_plural = "Payment Providers"
        ordering = ['name']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({self.code}) - {status}"
