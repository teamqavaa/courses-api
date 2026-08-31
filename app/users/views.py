from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import (
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserListSerializer,
    UserAdminSerializer,
    UserAdminCreateSerializer,
    UserBulkRowSerializer,
    UserBulkRequestSerializer,
    UserBulkResultSerializer,
    get_tokens_for_user,
)
from .models import User


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(help_text="Email or phone number.")
    password = serializers.CharField()


class TokensSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


@extend_schema(
    request=LoginRequestSerializer,
    responses={200: TokensSerializer, 401: None},
    description="Authenticate a user by email or phone and password. Returns JWT access and refresh tokens.",
    examples=[
        OpenApiExample(
            "Login example",
            value={"username": "student@example.com", "password": "hunter2"},
            request_only=True,
        )
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"detail": "No account found"}, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"detail": "No account found"}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(get_tokens_for_user(user))


@extend_schema(
    request=UserRegistrationSerializer,
    responses={201: TokensSerializer, 400: None},
    description="Register a new user. At least one of email or phone is required. Returns JWT access and refresh tokens.",
    examples=[
        OpenApiExample(
            "Register example",
            value={
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "phone": "+1234567890",
                "password": "hunter2",
            },
            request_only=True,
        )
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["GET"],
    responses={200: UserProfileSerializer},
    description="Get the authenticated user's profile.",
)
@extend_schema(
    methods=["PATCH"],
    request=UserProfileSerializer,
    responses={200: UserProfileSerializer, 400: None},
    description="Partially update the authenticated user's profile.",
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == "GET":
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    data = request.data.copy()
    data.pop("avatar", None)

    serializer = UserProfileSerializer(request.user, data=data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    return Response(serializer.data)


@extend_schema(
    request=UserAdminCreateSerializer,
    responses={200: UserListSerializer(many=True), 201: UserAdminSerializer},
    description=(
        "Staff-only list of users with optional ?role=<value> filter, "
        "or create a single user."
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def admin_users(request):
    if request.method == "POST":
        serializer = UserAdminCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return Response(UserAdminSerializer(user).data, status=status.HTTP_201_CREATED)

    queryset = User.objects.all().order_by("-date_joined")
    role = request.query_params.get("role")
    if role:
        queryset = queryset.filter(role=role)
    serializer = UserListSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(
    responses={200: UserAdminSerializer},
    description="Staff-only retrieve or update one user's profile and permissions.",
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAdminUser])
def admin_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "GET":
        return Response(UserAdminSerializer(user).data)

    serializer = UserAdminSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(UserAdminSerializer(user).data)


USER_BULK_MAX_ROWS = 1000

# Empty CSV cells must land as NULL: the email/phone columns are unique and
# nullable, and existing rows use NULL rather than "".
_NULLABLE_TEXT_FIELDS = ("email", "phone", "full_name", "display_name")


def _set_initial_password(user: User, password: str | None) -> None:
    # A blank password on import means "no password yet", not "empty string".
    if password:
        user.set_password(password)
    else:
        user.set_unusable_password()


def _csv_blank_to_none(row: dict) -> dict:
    cleaned = dict(row)
    for key, value in cleaned.items():
        if isinstance(value, str):
            cleaned[key] = value.strip()
    for key in _NULLABLE_TEXT_FIELDS:
        if cleaned.get(key) == "":
            cleaned[key] = None
    # Emails are lowercase everywhere; row matching and the upsert key rely on it.
    if cleaned.get("email"):
        cleaned["email"] = cleaned["email"].lower()
    return cleaned


@extend_schema(
    request=UserBulkRequestSerializer,
    responses={201: UserBulkResultSerializer, 400: UserBulkResultSerializer},
    description=(
        "Bulk create or upsert users from parsed CSV rows. All-or-nothing: one "
        "invalid row aborts the whole request. Upsert matches on email, else "
        "phone; a blank password leaves the existing password untouched."
    ),
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_users_bulk(request):
    mode = request.data.get("mode", "create")
    if mode not in ("create", "upsert"):
        return Response(
            {"detail": "mode must be 'create' or 'upsert'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_rows = request.data.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        return Response(
            {"detail": "rows must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(raw_rows) > USER_BULK_MAX_ROWS:
        return Response(
            {"detail": f"Too many rows; the limit is {USER_BULK_MAX_ROWS}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    normalized = [_csv_blank_to_none(raw) if isinstance(raw, dict) else {} for raw in raw_rows]

    row_serializer = UserBulkRowSerializer(data=normalized, many=True)
    row_serializer.is_valid()
    errors = [
        {"row": i, "field": field, "message": " ".join(messages)}
        for i, row_errors in enumerate(row_serializer.errors)
        for field, messages in row_errors.items()
    ]

    # Duplicate keys inside the file would defeat either mode.
    seen_emails: dict[str, int] = {}
    seen_phones: dict[str, int] = {}
    for i, row in enumerate(normalized):
        for field, seen in (("email", seen_emails), ("phone", seen_phones)):
            value = row.get(field)
            if value:
                if value in seen:
                    errors.append({
                        "row": i,
                        "field": field,
                        "message": f"Duplicate {field} in file; first seen on row {seen[value] + 2} (header line included).",
                    })
                else:
                    seen[value] = i

    # Create mode must not collide with existing rows; check before writing.
    if mode == "create":
        emails = [row["email"] for row in normalized if row.get("email")]
        phones = [row["phone"] for row in normalized if row.get("phone")]
        if emails:
            # iexact catches legacy rows stored with mixed case.
            existing = set(
                User.objects.filter(
                    Q(*[Q(email__iexact=email) for email in emails], _connector=Q.OR)
                ).values_list("email", flat=True)
            )
            existing = {email.lower() for email in existing}
            for i, row in enumerate(normalized):
                if row.get("email") and row["email"] in existing:
                    errors.append({
                        "row": i,
                        "field": "email",
                        "message": "A user with this email already exists.",
                    })
        if phones:
            existing = set(
                User.objects.filter(phone__in=phones).values_list("phone", flat=True)
            )
            for i, row in enumerate(normalized):
                if row.get("phone") in existing:
                    errors.append({
                        "row": i,
                        "field": "phone",
                        "message": "A user with this phone already exists.",
                    })

    if errors:
        return Response(
            {"created": 0, "updated": 0, "errors": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created = updated = 0
    write_errors: list[dict] = []
    try:
        with transaction.atomic():
            for i, row in enumerate(normalized):
                try:
                    fields = {
                        "full_name": row.get("full_name"),
                        "display_name": row.get("display_name"),
                        "phone": row.get("phone"),
                        "role": row.get("role", User.Role.STUDENT),
                        "language": row.get("language") or "en",
                        "is_active": row.get("is_active", True),
                        "is_staff": row.get("is_staff", False),
                    }
                    password = row.get("password") or None

                    if mode == "create":
                        user = User(**fields, email=row.get("email"))
                        _set_initial_password(user, password)
                        user.save()
                        created += 1
                        continue

                    # Upsert matches on email when present, else phone. Rows
                    # matching nothing fall through to creation.
                    if row.get("email"):
                        user = User.objects.filter(email__iexact=row["email"]).first()
                    else:
                        user = User.objects.filter(phone=row["phone"]).first()

                    if user is None:
                        user = User(**fields, email=row.get("email"))
                        _set_initial_password(user, password)
                        user.save()
                        created += 1
                    else:
                        for key, value in fields.items():
                            setattr(user, key, value)
                        if row.get("email"):
                            user.email = row["email"]
                        if password:
                            user.set_password(password)
                        user.save()
                        updated += 1
                except ValidationError as exc:
                    # model.save() runs full_clean(); a DB-level rejection maps
                    # to a row error and rolls the whole import back.
                    messages = getattr(exc, "messages", None) or [str(exc)]
                    write_errors.append({
                        "row": i,
                        "field": "non_field_errors",
                        "message": "; ".join(messages),
                    })
            if write_errors:
                raise IntegrityError("bulk user import aborted")
    except IntegrityError:
        return Response(
            {"created": 0, "updated": 0, "errors": write_errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        UserBulkResultSerializer({"created": created, "updated": updated, "errors": []}).data,
        status=status.HTTP_201_CREATED,
    )
