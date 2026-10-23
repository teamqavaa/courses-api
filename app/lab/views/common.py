from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework.exceptions import AuthenticationFailed

from lab.models import Lab


def get_user_id(request):
    user_id = str(getattr(request.user, 'id', '') or '').strip()
    if not user_id:
        raise AuthenticationFailed('Le token SSO ne contient pas de champ sub.')
    return user_id


def get_lab(lab_ref, published_only=True):
    queryset = Lab.objects.prefetch_related('objectives', 'skills')
    if published_only:
        queryset = queryset.filter(status=Lab.Status.PUBLISHED)

    reference = str(lab_ref)
    try:
        return queryset.get(slug=reference)
    except Lab.DoesNotExist:
        pass

    try:
        return queryset.get(pk=reference)
    except (Lab.DoesNotExist, ValidationError, ValueError):
        raise Http404('Lab introuvable.')
