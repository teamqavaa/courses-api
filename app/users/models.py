import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("At least one of email or phone must be provided.")

        email = self.normalize_email(email) if email else None
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, phone=phone, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Admin"
        PARENT = "parent", "Parent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    display_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    language = models.CharField(max_length=10, default="en")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="users_user_email_unique_ci",
                condition=models.Q(email__isnull=False),
            )
        ]

    def clean(self):
        super().clean()
        if not self.email and not self.phone:
            raise ValidationError("At least one of email or phone must be provided.")

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email or self.phone or str(self.id)
