from django.db import models

from quiz_questions.models import Question


class QuizOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='question',
    )
    text = models.CharField(
        max_length=500,
        verbose_name='option text',
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name='correct answer',
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name='display order',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'quiz option'
        verbose_name_plural = 'quiz options'
        ordering = ['order']

    def __str__(self):
        return self.text[:50]
