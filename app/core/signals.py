"""
Signaux partagés entre les apps de courses-api.

Ils évitent les imports croisés : `lab/` et `quizzes/` émettent, `enrollments/` écoute
(enrollments/receivers.py, branché dans EnrollmentsConfig.ready()).
"""
from django.dispatch import Signal

# Une activité notée a été réussie par un utilisateur.
# Arguments : user_id (sub SSO), lab=<lab.Lab> ou quiz=<quizzes.Quiz>, score (0-100 ou None).
activity_completed = Signal()

# Des inscriptions ont été créées sans post_save (bulk_create du paiement).
# Arguments : enrollments (liste d'Enrollment).
enrollments_created = Signal()
