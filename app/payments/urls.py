# app/payments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments.views import (
    PaymentProviderViewSet,
    PaymentViewSet,
    PaymentWebhookAPIView
)

# Configuration du routeur pour les ViewSets REST Framework
router = DefaultRouter()

# Endpoint pour récupérer les moyens de paiement disponibles (ex: /api/payments/providers/)
router.register(
    r'providers',
    PaymentProviderViewSet,
    basename='payment-provider'
)

# Endpoints pour consulter l'historique et initier un paiement (ex: /api/payments/)
router.register(
    r'',
    PaymentViewSet,
    basename='payment'
)

urlpatterns = [
    # Route pour les notifications Webhooks asynchrones des prestataires (Stripe, Wave, OM...)
    path(
        'webhook/<str:provider_code>/',
        PaymentWebhookAPIView.as_view(),
        name='payment-webhook'
    ),

    # Inclusion des routes automatiquement générées par le DefaultRouter
    path('', include(router.urls)),
]
