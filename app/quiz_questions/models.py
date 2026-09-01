from django.db import models
from django.utils.text import slugify

from quizzes.models import Quiz
from question_types.models import TypeQuestion


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='quiz',
    )
    type_question = models.ForeignKey(
        TypeQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        verbose_name='question type',
    )
    text = models.TextField(
        verbose_name='question text',
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name='display order',
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name='slug',
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='Active',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'quiz question'
        verbose_name_plural = 'quiz questions'
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.text[:50])
        super().save(*args, **kwargs)

    def __str__(self):
        return self.text[:100]
