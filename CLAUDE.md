# CLAUDE.md — courses-api (service Cloud Run `contents-lab-api`)

API Django 5 / DRF des cours Ignite : catalogue (`courses`, `modules`, `lessons`, `videos`, …),
panier, commandes, paiements et **inscriptions avec progression de lecture**.
Consommée par le front `contents-lab` (server actions, Bearer du SSO).

## Authentification

Les requêtes portent l'access token du SSO Qavaa (JWT RS256) en `Authorization: Bearer` ou dans le
cookie `access_token`. `core/sso.py` vérifie la signature via le JWKS du SSO (`SSO_ISSUER`,
`SSO_JWKS_URL`) ; `SSOAuthentication` fournit `request.user` (`SSOUser` : `id` = `sub`, `roles`).
Les utilisateurs ne sont pas stockés ici : les modèles gardent le `sub` (`user_id`, CharField).

Droits (`SSOUser`) :
- `is_admin` : rôle `admin`, `superadmin` ou `superuser`, **ou** claim `is_staff` / `is_superuser` à `true` ;
- `is_instructor` : rôle `instructor` (ou admin).

`OptionalSSOAuthentication` (catalogue) : un token absent, expiré ou invalide rend la requête
anonyme au lieu de la rejeter ; les écritures restent bloquées par les permissions.

## Gestion des cours (`courses/`, `core/permissions.py`)

Statuts d'un cours : `draft` → `review` (soumis par l'instructeur) → `published` (validé par un admin).

| Route | Règle |
|---|---|
| `GET /api/courses/`, `GET /api/courses/<slug>/` | public : cours `published` uniquement ; un instructeur voit aussi les siens, un admin tout |
| `GET /api/courses/search/?q=&limit=` | public : **recherche** dans les cours `published` (jamais de brouillon, même pour son auteur). Chaque mot doit apparaître dans le titre, sous-titre, description, `instructor_name`, catégorie, tag, module ou leçon publiés ; titre d'abord. `q` < 2 caractères → aucun résultat ; `limit` 20 par défaut, 50 max. Réponse `{query, count, results: [{id, slug, title, subtitle, level, language, thumbnail, instructor_name, category_details, average_rating, total_students, lessons_count}]}` |
| `GET /api/courses/manage/?status=&search=` | instructeur : ses cours ; admin : tous (403 pour un étudiant) — compteurs `modules_count`, `lessons_count` |
| `POST /api/courses/` | instructeur ou admin ; le cours appartient au `sub` du token (`user_id`) ; un instructeur ne peut pas créer en `published` (403) |
| `PATCH` / `DELETE /api/courses/<slug>/` | admin, ou instructeur propriétaire ; `DELETE` d'un cours déjà commandé → 409 |
| `POST /api/courses/<slug>/status/` `{status}` | propriétaire : `draft` ↔ `review` ; admin : tous les statuts |
| `POST/PATCH/DELETE /api/modules/`, `/api/lessons/`, `/api/videos/` | admin, ou instructeur propriétaire du cours parent (`CanManageCourses`, `ensure_can_edit_course`) |

Champs de la page détail (front `/courses/<slug>`) :
- `instructor_name` : nom affiché du formateur, copié du claim `name` du token à la création (lecture
  seule ; complété à la première modification par le propriétaire pour les anciens cours).
- `prerequisites`, `target_audience` : textes libres saisis dans « Manage courses ».
- `user_email` et `user_roles` ne sont renvoyés qu'au propriétaire du cours et aux admins
  (données personnelles du formateur masquées au public).

Pour protéger une nouvelle ressource rattachée à un cours : `permission_classes = [CanManageCourses]`
et `ensure_can_edit_course(request.user, course_of(objet))` dans `perform_create` / `perform_update`.

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
docker compose run --rm app sh -c "python manage.py test courses"      # gestion des cours et droits
docker compose run --rm app sh -c "python manage.py makemigrations"
```

Tests d'API authentifiés : réutiliser `make_token()` / `FakeSigningKey` de `core/tests.py` et patcher
`core.sso._jwks_client.get_signing_key_from_jwt`.

## Exécution de code locale (Piston)

Les endpoints `/api/lab/` délèguent l'exécution à Piston via `PISTON_URL`. Le stack local
est autonome dans `infrastructure/piston/` (aucune dépendance à Digital-Readiness-Lab) :

```bash
docker compose -f infrastructure/piston/docker-compose.yml up -d
sh infrastructure/piston/install-runtimes.sh
```

Runtimes requis : Python `3.12.0`, PHP `8.2.3`, TypeScript `5.0.3`. Voir
`infrastructure/piston/README.md` pour les ports et le dépannage. Sans Piston joignable,
l'endpoint d'exécution renvoie `502`.

Déploiement (`.github/workflows/deploy.yml`, push sur `main`) : build → job Cloud Run
`migrate` + seeds → service Cloud Run. La production doit fournir un Piston privé via
`PISTON_URL` ; Cloud Run n'héberge pas Piston.
