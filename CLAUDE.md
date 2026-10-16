# CLAUDE.md — courses-api (service Cloud Run `contents-lab-api`)

API Django 5 / DRF des cours Ignite : catalogue (`courses`, `modules`, `lessons`, `videos`, …),
panier, commandes, paiements et **inscriptions avec progression de lecture**.
Consommée par le front `contents-lab` (server actions, Bearer du SSO).

## Authentification

Les requêtes portent l'access token du SSO Qavaa (JWT RS256) en `Authorization: Bearer` ou dans le
cookie `access_token`. `core/sso.py` vérifie la signature via le JWKS du SSO (`SSO_ISSUER`,
`SSO_JWKS_URL`) ; `SSOAuthentication` fournit `request.user` (`SSOUser` : `id` = `sub`, `roles`).
Les utilisateurs ne sont pas stockés ici : les modèles gardent le `sub` (`user_id`, CharField).

## Inscriptions et progression (`enrollments/`)

Modèles :
- `Enrollment` (`user_id`, `course`, `order`, `progress_percentage`, `status`, `last_accessed_at`).
- `LessonProgress` (`enrollment`, `lesson`, `position_seconds`, `is_completed`, `completed_at`),
  unique par (inscription, leçon).

Règles (`enrollments/services.py`) :
- leçons comptées = leçons publiées de modules publiés du cours ;
- `progress_percentage` = leçons terminées / leçons comptées × 100, recalculé à chaque enregistrement ;
- marquer une leçon terminée est idempotent ; `position_seconds` absent = position conservée ;
- les inscriptions `suspended` sont exclues.

Endpoints (authentification SSO obligatoire, uniquement les inscriptions du `sub` du token) :

| Route | Réponse |
|---|---|
| `GET /api/enrollments/` | inscriptions triées par dernier accès : `progress_percentage`, `total_lessons`, `completed_lessons`, `total_duration_minutes`, `completed_lesson_ids`, `last_lesson {id, slug, title, position_seconds}`, `course {id, slug, title, thumbnail, category {name, slug}, …}` |
| `GET /api/enrollments/<slug du cours>/` | une inscription (404 si non inscrit) |
| `POST /api/enrollments/<slug>/progress/` | corps `{lesson_id, position_seconds?, completed?}` → `{lesson_progress, enrollment}` ; 400 si la leçon n'appartient pas au cours, 404 si non inscrit |
| `GET /api/enrollments/stats/?days=7` | `enrolled_courses`, `completed_courses`, `in_progress_courses`, `completed_lessons`, `learning_minutes`, `average_progress`, `activity [{date, lessons_completed, minutes}]` (1 à 90 jours) |

`GET /api/courses/my-enrollments/` (liste des cours inscrits, format catalogue) reste disponible.

## Commandes

```bash
docker compose up                                                   # API sur :8080
docker compose run --rm app sh -c "python manage.py test"           # tests
docker compose run --rm app sh -c "python manage.py test enrollments"
docker compose run --rm app sh -c "python manage.py makemigrations"
```

Tests d'API authentifiés : réutiliser `make_token()` / `FakeSigningKey` de `core/tests.py` et patcher
`core.sso._jwks_client.get_signing_key_from_jwt`.

Déploiement (`.github/workflows/deploy.yml`, push sur `main`) : build → job Cloud Run
`migrate` + seeds → service Cloud Run.
