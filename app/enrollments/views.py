from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import Enrollment
from .serializers import EnrollmentSerializer
from core.utils import get_user_sub_from_request

class EnrollmentViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    ViewSet pour les inscriptions basé sur le SSO cookie.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = []
    authentication_classes = []

    def get_queryset(self):
        try:
            user_sub = get_user_sub_from_request(self.request)
        except AuthenticationFailed:
            return Enrollment.objects.none()

        return Enrollment.objects.filter(
            user_id=user_sub,
            status='active'
        ).select_related('course')
