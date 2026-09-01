from django.db import models

from quizzes.models import Quiz


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='quiz',
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='started at',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='completed at',
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='completed',
    )

    class Meta:
        verbose_name = 'quiz attempt'
        verbose_name_plural = 'quiz attempts'
        ordering = ['-started_at']

    def __str__(self):
        return f"Attempt #{self.pk} for {self.quiz}"
