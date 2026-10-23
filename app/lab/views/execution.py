import os
from datetime import timedelta

import requests
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lab.models import RateLimit
from lab.serializers import (
    ExecuteErrorSerializer,
    ExecuteRequestSerializer,
    ExecuteResponseSerializer,
)

from .common import get_user_id

RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = timedelta(minutes=1)


def _piston_url():
    configured = getattr(settings, 'PISTON_URL', None) or os.getenv('PISTON_URL')
    return (configured or 'http://localhost:2000').rstrip('/')


def _check_rate_limit(user_id):
    now = timezone.now()
    record = RateLimit.objects.filter(pk=user_id).first()
    if record is None:
        try:
            with transaction.atomic():
                RateLimit.objects.create(
                    user_id=user_id,
                    request_count=1,
                    window_start=now,
                )
            return True
        except IntegrityError:
            pass

    with transaction.atomic():
        record = RateLimit.objects.select_for_update().get(pk=user_id)
        if now - record.window_start >= RATE_LIMIT_WINDOW:
            record.request_count = 1
            record.window_start = now
            record.save(update_fields=['request_count', 'window_start', 'updated_at'])
            return True
        if record.request_count >= RATE_LIMIT_REQUESTS:
            return False
        record.request_count += 1
        record.save(update_fields=['request_count', 'updated_at'])
        return True


def _validation_error(serializer):
    errors = serializer.errors
    first = next(iter(errors.values()))
    if isinstance(first, (list, tuple)) and first:
        first = first[0]
    return Response({'error': str(first)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=ExecuteRequestSerializer,
    responses={
        200: ExecuteResponseSerializer,
        400: ExecuteErrorSerializer,
        429: ExecuteErrorSerializer,
        502: ExecuteErrorSerializer,
        504: ExecuteErrorSerializer,
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_code(request):
    user_id = get_user_id(request)
    serializer = ExecuteRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return _validation_error(serializer)

    data = serializer.validated_data

    if not _check_rate_limit(user_id):
        return Response(
            {'error': 'Rate limit exceeded. Please wait before running again.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    payload = {
        'language': data['language'],
        'version': data['version'],
        'files': [{'name': data['filename'], 'content': data['code']}],
    }

    try:
        response = requests.post(
            f'{_piston_url()}/api/v2/execute',
            json=payload,
            timeout=getattr(settings, 'PISTON_TIMEOUT_SECONDS', 30),
        )
    except requests.Timeout:
        return Response(
            {'error': 'Execution timed out.'},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except requests.RequestException:
        return Response(
            {'error': 'Could not reach the code execution service.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if response.status_code >= 500:
        return Response(
            {'error': 'The code execution service returned an error.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    if 400 <= response.status_code < 500:
        try:
            message = response.json().get('message') or response.text
        except ValueError:
            message = response.text
        return Response(
            {'error': message or 'Execution request rejected.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        return Response(response.json())
    except ValueError:
        return Response(
            {'error': 'Unexpected response from the code execution service.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
