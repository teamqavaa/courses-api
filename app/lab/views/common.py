from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from rest_framework.exceptions import AuthenticationFailed

from lab.models import Lab


def get_user_id(request):
    user_id = str(getattr(request.user, 'id', '') or '').strip()
    if not user_id:
        raise AuthenticationFailed('Le token SSO ne contient pas de champ sub.')
    return user_id


def visible_labs(user=None):
    """
    Labs visibles par l'utilisateur : un admin (rôle admin/superadmin/superuser, is_staff ou
    is_superuser) voit tout, un instructeur les labs publiés et les siens, les autres les publiés.
    """
    queryset = Lab.objects.prefetch_related('objectives', 'skills')
    if getattr(user, 'is_admin', False):
        return queryset
    if getattr(user, 'is_instructor', False) and getattr(user, 'id', None):
        return queryset.filter(Q(status=Lab.Status.PUBLISHED) | Q(user_id=str(user.id)))
    return queryset.filter(status=Lab.Status.PUBLISHED)


def get_lab(lab_ref, user=None):
    """Lab par slug (ou ancien UUID), parmi ceux que l'utilisateur peut voir ; 404 sinon."""
    queryset = visible_labs(user)

    reference = str(lab_ref)
    try:
        return queryset.get(slug=reference)
    except Lab.DoesNotExist:
        pass

    try:
        return queryset.get(pk=reference)
    except (Lab.DoesNotExist, ValidationError, ValueError):
        raise Http404('Lab introuvable.')
