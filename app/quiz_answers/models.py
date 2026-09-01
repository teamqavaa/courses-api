from django.db import models

from quiz_attempts.models import QuizAttempt
from quiz_questions.models import Question
from quiz_options.models import QuizOption


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='quiz attempt',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='question',
    )
    option = models.ForeignKey(
        QuizOption,
        on_delete=models.CASCADE,
        related_name='selected_in',
        verbose_name='selected option',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'quiz answer'
        verbose_name_plural = 'quiz answers'
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"Answer to Q{self.question_id} in Attempt #{self.attempt_id}"
