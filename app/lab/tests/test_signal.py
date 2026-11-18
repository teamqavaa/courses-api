"""
POST /api/sessions/<uuid>/complete/ émet core.signals.activity_completed, sans rien changer d'autre
(même réponse, même code HTTP). lab/ n'importe pas enrollments/ : seul le signal est vérifié ici
(le marquage des leçons est testé dans enrollments/tests_lab_completion.py).
"""
import uuid
from unittest.mock import patch

from rest_framework.test import APITestCase

from core.signals import activity_completed
from core.tests import USER_ID, FakeSigningKey, make_token
from lab.models import Lab


class SignalRecorder:
    """Enregistre les envois du signal pendant un test."""

    def __init__(self):
        self.calls = []

    def __call__(self, sender, **kwargs):
        self.calls.append({'sender': sender, **kwargs})


@patch('core.sso._jwks_client.get_signing_key_from_jwt', return_value=FakeSigningKey())
class CompleteSessionSignalTests(APITestCase):

    def setUp(self):
        self.lab = Lab.objects.create(title='Listes', status=Lab.Status.PUBLISHED)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token()}')
        self.recorder = SignalRecorder()
        activity_completed.connect(self.recorder, dispatch_uid='test_recorder')
        self.addCleanup(activity_completed.disconnect, dispatch_uid='test_recorder')

    def test_complete_emits_activity_completed(self, _):
        self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        self.assertEqual(len(self.recorder.calls), 1)
        call = self.recorder.calls[0]
        self.assertIs(call['sender'], Lab)
        self.assertEqual(call['user_id'], USER_ID)
        self.assertEqual(call['lab'], self.lab)
        self.assertIn('score', call)

    def test_complete_response_is_unchanged(self, _):
        response = self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'ok': True})

    def test_completing_again_emits_again_and_stays_ok(self, _):
        self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        response = self.client.post(f'/api/sessions/{self.lab.id}/complete/')
        self.assertEqual(response.data, {'ok': True})
        self.assertEqual(len(self.recorder.calls), 2)

    def test_uncomplete_and_reset_do_not_emit(self, _):
        self.client.post(f'/api/sessions/{self.lab.id}/', {'current_code': 'x'}, format='json')
        self.client.post(f'/api/sessions/{self.lab.id}/uncomplete/')
        self.client.post(f'/api/sessions/{self.lab.id}/reset/')
        self.assertEqual(self.recorder.calls, [])

    def test_unknown_lab_does_not_emit(self, _):
        response = self.client.post(f'/api/sessions/{uuid.uuid4()}/complete/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.recorder.calls, [])

    def test_draft_lab_of_someone_else_does_not_emit(self, _):
        draft = Lab.objects.create(title='Brouillon', status=Lab.Status.DRAFT, user_id='autre')
        response = self.client.post(f'/api/sessions/{draft.id}/complete/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.recorder.calls, [])
