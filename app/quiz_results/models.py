from django.db import models

from quiz_answers.models import QuizAnswer


class Result(models.Model):
    # Each answer has exactly one result — enforced by OneToOneField.
    answer = models.OneToOneField(
        QuizAnswer,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name='quiz answer',
    )
    is_correct = models.BooleanField(
        verbose_name='is correct',
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='score',
    )
    feedback = models.TextField(
        blank=True,
        verbose_name='feedback',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'quiz result'
        verbose_name_plural = 'quiz results'

    def __str__(self):
        status = "Correct" if self.is_correct else "Incorrect"
        return f"Result for Answer #{self.answer_id}: {status}"
