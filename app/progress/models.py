import uuid

from django.db import models

from courses.models import Course


class CourseProgress(models.Model):
    """
    Per-user completion state for a course.

    user_id is the UUID `user_id` claim of the JWT issued by the SSO backend
    (Digital-Readiness-Lab); no local user row exists in this service.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(verbose_name="SSO user id")
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="progresses",
        verbose_name="course",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        verbose_name="status",
    )
    progress_percent = models.PositiveIntegerField(
        default=0,
        verbose_name="progress percent",
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="completed at",
    )
    # Drives "most recently touched" ordering for the dashboard's
    # continue-where-you-left-off card.
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated at")

    class Meta:
        verbose_name = "course progress"
        verbose_name_plural = "course progress"
        ordering = ["-updated_at"]
        unique_together = [("user_id", "course")]

    def __str__(self):
        return f"{self.user_id}:{self.course_id}={self.status}"
