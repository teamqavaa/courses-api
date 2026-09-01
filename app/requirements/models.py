from django.db import models

from courses.models import Course


class CourseRequirement(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name='course',
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name='display order',
    )
    content = models.CharField(
        max_length=500,
        verbose_name='requirement',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'course requirement'
        verbose_name_plural = 'course requirements'
        ordering = ['order']

    def __str__(self):
        return self.content[:50]
