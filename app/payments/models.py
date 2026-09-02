import uuid
from django.db import models
from django.core.exceptions import ValidationError
from orders.models import Order
from payment_providers.models import PaymentProvider


class Payment(models.Model):
    """
    Modèle représentant une tentative de transaction bancaire ou Mobile Money.
    Dissocié de Order (contrat commercial) et lié à PaymentProvider.
    """
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESSFUL = 'SUCCESSFUL', 'Successful'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="UUID Identifier"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name="Associated Order",
        help_text="Commande liée à cette tentative de paiement"
    )
    provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name="Payment Provider",
        help_text="Prestataire utilisé pour exécuter la transaction"
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Payment Status"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Amount Paid"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        verbose_name="Currency Code",
        help_text="Code devise ISO 4217 (ex: XOF, EUR, USD)"
    )
    transaction_reference = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Provider Transaction Reference",
        help_text="Référence unique de transaction générée par le prestataire (ex: Stripe PaymentIntent ID)"
    )
    client_secret = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Client Secret / Redirect URL",
        help_text="Token ou URL de redirection transmis au Frontend/Mobile pour finaliser le paiement"
    )
    raw_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Raw Provider Response",
        help_text="Payload JSON complet retourné par le Webhook du prestataire pour audit"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Payment Date"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated"
    )

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']

    def clean(self):
        """Vérifie que le prestataire choisi est bien actif au moment de la création."""
        if self.provider_id and not self.provider.is_active:
            raise ValidationError(f"Le prestataire {self.provider.name} est actuellement désactivé.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Payment #{str(self.id)[:8]} - {self.provider.name} "
            f"({self.amount} {self.currency}) - [{self.get_status_display()}]"
        )
