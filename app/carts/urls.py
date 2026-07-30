# app/api_router.py (ou urls.py)
from rest_framework.routers import DefaultRouter
from carts.views import CartViewSet

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='cart')

urlpatterns = router.urls
