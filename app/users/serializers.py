from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema_field

from .models import User


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class UserRegistrationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="full_name", required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["name", "password", "email", "phone"]

    def validate(self, attrs):
        email = attrs.get("email")
        phone = attrs.get("phone")
        if not email and not phone:
            raise serializers.ValidationError(
                "At least one of email or phone must be provided."
            )
        # Match login's case-insensitive email behavior so casing never
        # yields a second account for the same address.
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        if phone and User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        return get_tokens_for_user(instance)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "display_name",
            "email",
            "phone",
            "role",
            "is_active",
            "is_staff",
            "date_joined",
        ]


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "display_name",
            "bio",
            "birth_date",
            "city",
            "country",
            "language",
            "role",
            "email",
            "phone",
            "is_active",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UserAdminCreateSerializer(serializers.ModelSerializer):
    """Single-user creation by a staff member. Mirrors the bulk row rules."""

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            "display_name",
            "email",
            "phone",
            "role",
            "is_active",
            "is_staff",
            "language",
            "password",
        ]
        extra_kwargs = {
            "full_name": {"required": False, "allow_blank": True, "allow_null": True},
            "display_name": {"required": False, "allow_blank": True, "allow_null": True},
            "email": {"required": False, "allow_blank": True, "allow_null": True},
            "phone": {"required": False, "allow_blank": True, "allow_null": True},
            "role": {"required": False, "default": User.Role.STUDENT},
            "is_active": {"required": False, "default": True},
            "is_staff": {"required": False, "default": False},
            "language": {"required": False, "default": "en"},
        }

    def validate(self, attrs):
        email = attrs.get("email")
        phone = attrs.get("phone")
        if not email and not phone:
            raise serializers.ValidationError(
                "At least one of email or phone must be provided."
            )
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        if phone and User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                {"phone": "A user with this phone already exists."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        # Blank cells behave like the CSV import: NULL, never the empty string.
        for key in ("email", "phone", "full_name", "display_name"):
            if validated_data.get(key) == "":
                validated_data[key] = None
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user


class UserBulkRowSerializer(serializers.Serializer):
    """One parsed CSV row of a bulk user import. Blank cells arrive as None."""

    full_name = serializers.CharField(required=False, allow_null=True, max_length=255)
    display_name = serializers.CharField(required=False, allow_null=True, max_length=100)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_null=True, max_length=20)
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    language = serializers.CharField(required=False, allow_blank=True, max_length=10)
    password = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("phone"):
            raise serializers.ValidationError(
                "At least one of email or phone must be provided."
            )
        return attrs


class UserBulkRequestSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["create", "upsert"], default="create")
    rows = UserBulkRowSerializer(many=True)


class UserBulkResultSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.DictField())


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "display_name",
            "avatar",
            "bio",
            "birth_date",
            "city",
            "country",
            "language",
            "role",
            "is_staff",
        ]
        read_only_fields = ["id"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_avatar(self, obj):
        return None
