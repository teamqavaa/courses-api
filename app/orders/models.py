import uuid
from django.db import models


class Order(models.Model):
    """
    Modèle représentant la commande (contrat commercial).
    Ne contient plus les détails techniques de la transaction bancaire.
    """
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Payment'
        PAID = 'PAID', 'Paid'
        CANCELLED = 'CANCELLED', 'Cancelled'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="UUID Identifier"
    )
    # Stocke le 'sub' extrait de l'access_token (aligné avec le modèle Cart)
    user_id = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="ID Utilisateur (sub)"
    )
    user_email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Email de l'utilisateur"
    )
    user_role = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Rôle principal"
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name="Status"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total Amount"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        verbose_name="Currency"
    )
    discount = models.ForeignKey(
        'discounts.Discount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Applied Discount"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Discount Amount"
    )
    discount_code_snapshot = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Discount Code Snapshot"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Order Date"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated"
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
        ]

    def __str__(self):
        identifier = self.user_email or self.user_id
        return f"Order #{str(self.id)[:8]} - {identifier} ({self.get_status_display()})"
