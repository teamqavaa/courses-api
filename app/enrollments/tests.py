"""
Tests des inscriptions de l'utilisateur connecté et de la progression de lecture
(GET /api/enrollments/, POST /api/enrollments/<slug>/progress/, GET /api/enrollments/stats/).
"""
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from categories.models import Category
from core.tests import USER_ID, FakeSigningKey, make_token
from courses.models import Course
from lessons.models import Lesson
from modules.models import Module
from .models import Enrollment, LessonProgress

OTHER_USER_ID = '00000000-0000-0000-0000-000000000002'


def create_course(title, category, lessons=4):
    course = Course.objects.create(
        category=category, title=title, description='desc', price='10.00',
        user_id='instructor', user_email='instructor@qavaa.com', status='published',
    )
    module = Module.objects.create(course=course, title='Module 1', order=1)
    for index in range(1, lessons + 1):
        Lesson.objects.create(module=module, title=f'Leçon {index}', order=index, duration_in_minutes=10)
    return course


@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class EnrollmentApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token()}')
        category = Category.objects.create(name='Front End', slug='front-end')
        self.course = create_course('React avancé', category)
        self.other_course = create_course('Design UI', category, lessons=2)
        self.enrollment = Enrollment.objects.create(user_id=USER_ID, course=self.course)
        Enrollment.objects.create(user_id=OTHER_USER_ID, course=self.other_course)
        self.lessons = list(Lesson.objects.filter(module__course=self.course).order_by('order'))
        self.url = f'/api/enrollments/{self.course.slug}/progress/'

    def test_authentication_required(self, _):
        res = APIClient().get('/api/enrollments/')
        self.assertIn(res.status_code, (401, 403))

    def test_list_returns_only_my_enrollments_with_progress(self, _):
        res = self.client.get('/api/enrollments/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        item = res.data[0]
        self.assertEqual(item['course']['slug'], self.course.slug)
        self.assertEqual(item['course']['category']['name'], 'Front End')
        self.assertEqual(item['total_lessons'], 4)
        self.assertEqual(item['completed_lessons'], 0)
        self.assertEqual(item['total_duration_minutes'], 40)
        self.assertEqual(item['progress_percentage'], 0)
        self.assertEqual(item['last_lesson']['id'], str(self.lessons[0].id))

    def test_completing_a_lesson_updates_percentage(self, _):
        res = self.client.post(self.url, {'lesson_id': str(self.lessons[0].id), 'completed': True}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['enrollment']['completed_lessons'], 1)
        self.assertEqual(res.data['enrollment']['progress_percentage'], 25.0)
        self.enrollment.refresh_from_db()
        self.assertEqual(float(self.enrollment.progress_percentage), 25.0)

    def test_completing_twice_is_idempotent(self, _):
        payload = {'lesson_id': str(self.lessons[0].id), 'completed': True}
        self.client.post(self.url, payload, format='json')
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.data['enrollment']['progress_percentage'], 25.0)
        self.assertEqual(LessonProgress.objects.count(), 1)

    def test_position_is_saved_and_becomes_last_lesson(self, _):
        lesson = self.lessons[2]
        res = self.client.post(self.url, {'lesson_id': str(lesson.id), 'position_seconds': 95}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['enrollment']['last_lesson']['id'], str(lesson.id))
        self.assertEqual(res.data['enrollment']['last_lesson']['position_seconds'], 95)
        self.assertEqual(res.data['enrollment']['progress_percentage'], 0)

    def test_lesson_of_another_course_is_rejected(self, _):
        foreign = Lesson.objects.filter(module__course=self.other_course).first()
        res = self.client.post(self.url, {'lesson_id': str(foreign.id), 'completed': True}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_cannot_track_progress_on_a_course_i_am_not_enrolled_in(self, _):
        lesson = Lesson.objects.filter(module__course=self.other_course).first()
        res = self.client.post(
            f'/api/enrollments/{self.other_course.slug}/progress/',
            {'lesson_id': str(lesson.id), 'completed': True}, format='json',
        )
        self.assertEqual(res.status_code, 404)

    def test_stats(self, _):
        for lesson in self.lessons[:2]:
            self.client.post(self.url, {'lesson_id': str(lesson.id), 'completed': True}, format='json')
        res = self.client.get('/api/enrollments/stats/?days=7')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['enrolled_courses'], 1)
        self.assertEqual(res.data['in_progress_courses'], 1)
        self.assertEqual(res.data['completed_lessons'], 2)
        self.assertEqual(res.data['learning_minutes'], 20)
        self.assertEqual(res.data['average_progress'], 50.0)
        self.assertEqual(len(res.data['activity']), 7)
        self.assertEqual(res.data['activity'][-1]['lessons_completed'], 2)
        self.assertEqual(res.data['activity'][-1]['minutes'], 20)
