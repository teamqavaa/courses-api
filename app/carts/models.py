from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError



class Cart(models.Model):
    """
    Model representant le panier global d'un user
    chaque user connecté possède un seul actif panier (OneToOneField)
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name ='cart',
        verbose_name='user'
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
        verbose_name = "cart"
        verbose_name_plural = "carts"

