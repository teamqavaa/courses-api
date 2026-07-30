import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from courses.models import Course


class Discount(models.Model):
    """
    Modèle représentant un code promo / réduction administrable.
    Identifié par un UUID v4 unique.
    Peut s'appliquer soit à un cours spécifique, soit à l'ensemble du panier.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant UUID"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code promo",
        help_text="Ex: WELCOME2026 ou PYTHON50"
    )
    discount_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Pourcentage de réduction (%)",
        help_text="Valeur comprise entre 1 et 100"
    )

    # Cible du coupon (Optionnel)
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupons',
        verbose_name="Cours spécifique",
        help_text="Laissez vide si le coupon s'applique globalement à tout le panier."
    )

    active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Permet de désactiver manuellement le code promo."
    )
    valid_from = models.DateTimeField(
        verbose_name="Valide à partir du"
    )
    valid_to = models.DateTimeField(
        verbose_name="Valide jusqu'au"
    )
    max_uses = models.PositiveIntegerField(
        default=0,
        verbose_name="Utilisations maximales",
        help_text="Mettez 0 pour un nombre illimité d'utilisations."
    )
    used_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'utilisations effectuées",
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )

    class Meta:
        verbose_name = "Code Promo"
        verbose_name_plural = "Codes Promo"
        ordering = ['-created_at']

    def __str__(self):
        target = f" (Cours: {self.course.title})" if self.course else " (Global Panier)"
        return f"{self.code} (-{self.discount_percentage}%){target}"

    @property
    def is_valid(self) -> bool:
        """
        Vérifie dynamiquement si le coupon remplit toutes les conditions de validité :
        1. Est-il actif ?
        2. Sommes-nous dans la période de validité (entre valid_from et valid_to) ?
        3. Le nombre maximal d'utilisations est-il atteint ?
        """
        now = timezone.now()
        if not self.active:
            return False
        if not (self.valid_from <= now <= self.valid_to):
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:  # noqa: SIM103
            return False
        return True
