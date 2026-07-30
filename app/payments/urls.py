# app/payments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentProviderViewSet,
    PaymentViewSet,
    PaymentWebhookAPIView
)

# Router principal
router = DefaultRouter()

# 1. /api/payments/providers/
router.register(
    r'providers',
    PaymentProviderViewSet,
    basename='payment-provider'
)

# 2. /api/payments/
router.register(
    r'',
    PaymentViewSet,
    basename='payment'
)

urlpatterns = [
    # Webhook prioritaire (doit rester au-dessus des URLs du router)
    path(
        'webhook/<str:provider_code>/',
        PaymentWebhookAPIView.as_view(),
        name='payment-webhook'
    ),

    # Inclusions des routes auto-générées par le router (GET /, GET /{id}/, POST /initiate/)
    path('', include(router.urls)),
]
