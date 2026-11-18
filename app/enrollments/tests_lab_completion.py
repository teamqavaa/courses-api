"""
Parcours de bout en bout : terminer un lab par l'API (/api/sessions/<uuid>/complete/) marque terminée
la leçon LAB correspondante dans le cours où l'utilisateur est inscrit.
"""
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APITestCase

from categories.models import Category
from core.tests import USER_ID, FakeSigningKey, make_token
from courses.models import Course
from lab.models import Lab
from lessons.models import Lesson
from modules.models import Module
from .models import Enrollment, LessonProgress


@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class LabCompletionProgressTests(APITestCase):

    def setUp(self):
        category = Category.objects.create(name='Back End', slug='back-end')
        self.lab = Lab.objects.create(title='Listes', status=Lab.Status.PUBLISHED)
        self.course = Course.objects.create(
            category=category, title='Python', description='desc', price='10.00',
            user_id='instructor', status='published',
        )
        module = Module.objects.create(course=self.course, title='Module 1', order=1)
        Lesson.objects.create(module=module, title='Vidéo', order=1)
        self.lab_lesson = Lesson.objects.create(
            module=module, title='Pratique', order=2, lesson_type='LAB', lab=self.lab,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token()}')

    def test_completing_the_lab_completes_the_lesson(self, _):
        enrollment = Enrollment.objects.create(user_id=USER_ID, course=self.course)
        response = self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        self.assertEqual(response.data, {'ok': True})
        self.assertTrue(LessonProgress.objects.get(enrollment=enrollment, lesson=self.lab_lesson).is_completed)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress_percentage, Decimal('50.00'))

        res = self.client.get(f'/api/enrollments/{self.course.slug}/')
        self.assertIn(str(self.lab_lesson.id), res.data['completed_lesson_ids'])

    def test_completing_the_lab_without_enrollment_only_updates_the_lab(self, _):
        response = self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LessonProgress.objects.exists())

    def test_uncompleting_the_lab_keeps_the_lesson_completed(self, _):
        enrollment = Enrollment.objects.create(user_id=USER_ID, course=self.course)
        self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        self.client.post(f'/api/sessions/{self.lab.id}/uncomplete/')
        self.assertTrue(LessonProgress.objects.get(enrollment=enrollment, lesson=self.lab_lesson).is_completed)
