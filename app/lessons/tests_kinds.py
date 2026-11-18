"""
Tests des leçons « lab » et du contenu texte (Lesson.lesson_type = LAB, Lesson.lab, Lesson.content).

Les leçons existantes restent des vidéos : lesson_type vaut VIDEO par défaut, lab est vide.
"""
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from categories.models import Category
from core.tests import FakeSigningKey, make_token
from courses.models import Course
from lab.models import Lab
from lessons.models import Lesson
from modules.models import Module

INSTRUCTOR_ID = '00000000-0000-0000-0000-0000000000a1'
OTHER_INSTRUCTOR_ID = '00000000-0000-0000-0000-0000000000a2'
ADMIN_ID = '00000000-0000-0000-0000-0000000000a3'
STUDENT_ID = '00000000-0000-0000-0000-0000000000a4'


def auth_client(sub, roles):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token(sub=sub, roles=roles)}')
    return client


class LessonKindModelTests(TestCase):

    def setUp(self):
        category = Category.objects.create(name='Back End', slug='back-end')
        course = Course.objects.create(
            category=category, title='Python', description='desc', price='10.00',
            user_id=INSTRUCTOR_ID, status='published',
        )
        self.module = Module.objects.create(course=course, title='Module 1', order=1)
        self.lab = Lab.objects.create(title='Listes', status=Lab.Status.PUBLISHED)

    def test_existing_lessons_stay_videos(self):
        lesson = Lesson.objects.create(module=self.module, title='Intro', order=1)
        self.assertEqual(lesson.lesson_type, Lesson.LessonType.VIDEO)
        self.assertIsNone(lesson.lab)
        self.assertEqual(lesson.content, '')

    def test_lab_lesson_requires_a_lab(self):
        lesson = Lesson(module=self.module, title='Pratique', order=1, lesson_type=Lesson.LessonType.LAB)
        with self.assertRaises(ValidationError):
            lesson.clean()
        lesson.lab = self.lab
        lesson.clean()

    def test_a_lab_used_by_a_lesson_cannot_be_deleted(self):
        Lesson.objects.create(
            module=self.module, title='Pratique', order=1, lesson_type=Lesson.LessonType.LAB, lab=self.lab,
        )
        with self.assertRaises(ProtectedError):
            self.lab.delete()
        self.assertEqual(list(self.lab.lessons.all()), list(Lesson.objects.filter(lab=self.lab)))


@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class LessonKindApiTests(TestCase):

    def setUp(self):
        category = Category.objects.create(name='Back End', slug='back-end')
        self.course = Course.objects.create(
            category=category, title='Python', description='desc', price='10.00',
            user_id=INSTRUCTOR_ID, status='published',
        )
        self.module = Module.objects.create(course=self.course, title='Module 1', order=1)
        self.video = Lesson.objects.create(module=self.module, title='Intro', order=1)
        self.lab = Lab.objects.create(title='Listes', status=Lab.Status.PUBLISHED)
        self.draft_lab = Lab.objects.create(title='Brouillon', status=Lab.Status.DRAFT, user_id=INSTRUCTOR_ID)
        self.instructor = auth_client(INSTRUCTOR_ID, ['instructor'])
        self.other_instructor = auth_client(OTHER_INSTRUCTOR_ID, ['instructor'])
        self.admin = auth_client(ADMIN_ID, ['admin'])
        self.student = auth_client(STUDENT_ID, ['student'])

    def lab_payload(self, **extra):
        return {
            'module': str(self.module.id), 'title': 'Pratique', 'order': 2,
            'lesson_type': 'LAB', 'lab': str(self.lab.id), **extra,
        }

    # --- Lecture ---------------------------------------------------------------

    def test_existing_video_lesson_is_serialized_as_before_plus_new_fields(self, _):
        res = self.student.get(f'/api/lessons/{self.video.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['lesson_type'], 'VIDEO')
        self.assertIsNone(res.data['lab'])
        self.assertIsNone(res.data['lab_details'])
        self.assertEqual(res.data['content'], '')
        for field in ('id', 'module', 'title', 'slug', 'description', 'duration_in_minutes',
                      'order', 'is_preview', 'is_published', 'video', 'created_at', 'updated_at'):
            self.assertIn(field, res.data)

    def test_lab_lesson_exposes_the_lab(self, _):
        lesson = Lesson.objects.create(
            module=self.module, title='Pratique', order=2, lesson_type='LAB', lab=self.lab,
        )
        res = self.student.get(f'/api/lessons/{lesson.id}/')
        self.assertEqual(res.data['lab'], self.lab.id)
        self.assertEqual(res.data['lab_details'], {
            'id': str(self.lab.id), 'slug': self.lab.slug, 'title': 'Listes', 'language': 'python',
        })

    def test_course_detail_lists_lab_lessons(self, _):
        Lesson.objects.create(module=self.module, title='Pratique', order=2, lesson_type='LAB', lab=self.lab)
        res = self.student.get(f'/api/courses/{self.course.slug}/')
        self.assertEqual(res.status_code, 200)
        lessons = res.data['modules'][0]['lessons']
        lab_lesson = next(item for item in lessons if item['lesson_type'] == 'LAB')
        self.assertEqual(lab_lesson['lab_details']['slug'], self.lab.slug)

    # --- Écriture --------------------------------------------------------------

    def test_owner_creates_a_lab_lesson(self, _):
        res = self.instructor.post('/api/lessons/', self.lab_payload(), format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(Lesson.objects.get(pk=res.data['id']).lab, self.lab)

    def test_lab_lesson_without_lab_is_rejected(self, _):
        res = self.instructor.post('/api/lessons/', self.lab_payload(lab=None), format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('lab', res.data)

    def test_unpublished_lab_is_rejected(self, _):
        res = self.instructor.post('/api/lessons/', self.lab_payload(lab=str(self.draft_lab.id)), format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('lab', res.data)

    def test_lab_is_cleared_when_the_lesson_is_no_longer_a_lab(self, _):
        lesson = Lesson.objects.create(module=self.module, title='Pratique', order=2, lesson_type='LAB', lab=self.lab)
        res = self.instructor.patch(f'/api/lessons/{lesson.id}/', {'lesson_type': 'ARTICLE'}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        lesson.refresh_from_db()
        self.assertIsNone(lesson.lab)

    def test_partial_update_keeps_the_lab(self, _):
        lesson = Lesson.objects.create(module=self.module, title='Pratique', order=2, lesson_type='LAB', lab=self.lab)
        res = self.instructor.patch(f'/api/lessons/{lesson.id}/', {'title': 'Pratique 2'}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        lesson.refresh_from_db()
        self.assertEqual(lesson.lab, self.lab)

    def test_text_content_is_saved(self, _):
        res = self.instructor.patch(
            f'/api/lessons/{self.video.id}/', {'lesson_type': 'ARTICLE', 'content': '# Titre'}, format='json',
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.video.refresh_from_db()
        self.assertEqual(self.video.content, '# Titre')

    def test_student_cannot_create_a_lab_lesson(self, _):
        res = self.student.post('/api/lessons/', self.lab_payload(), format='json')
        self.assertEqual(res.status_code, 403)

    def test_other_instructor_cannot_add_a_lab_lesson_to_my_course(self, _):
        res = self.other_instructor.post('/api/lessons/', self.lab_payload(), format='json')
        self.assertEqual(res.status_code, 403)

    # --- Suppression d'un lab utilisé ------------------------------------------

    def test_admin_cannot_delete_a_lab_used_by_a_lesson(self, _):
        Lesson.objects.create(module=self.module, title='Pratique', order=2, lesson_type='LAB', lab=self.lab)
        res = self.admin.delete(f'/api/labs/{self.lab.slug}/')
        self.assertEqual(res.status_code, 409)
        self.assertTrue(Lab.objects.filter(pk=self.lab.pk).exists())

    def test_unused_lab_is_still_deleted(self, _):
        res = self.admin.delete(f'/api/labs/{self.lab.slug}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Lab.objects.filter(pk=self.lab.pk).exists())
