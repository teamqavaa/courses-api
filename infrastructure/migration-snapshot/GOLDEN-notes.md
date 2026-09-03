# DRL golden baseline (Phase 0)

Captured from the running DRL backend on :8000.

## Endpoint inventory (from OpenAPI schema, drl_openapi.yaml)

/api/admin/labs/
/api/admin/labs/{id}/
/api/admin/labs/{lab_pk}/objectives/
/api/admin/labs/{lab_pk}/objectives/{id}/
/api/admin/skills/
/api/admin/skills/{id}/
/api/admin/users/
/api/admin/users/{id}/
/api/admin/users/bulk/
/api/auth/login/
/api/auth/refresh/
/api/execute/
/api/labs/
/api/labs/{lab_id}/
/api/progress/
/api/progress/{lab_id}/
/api/sessions/{lab_id}/
/api/sessions/{lab_id}/complete/
/api/sessions/{lab_id}/heartbeat/
/api/sessions/{lab_id}/reset/
/api/sessions/{lab_id}/uncomplete/
/api/skills/
/api/skills/{slug}/labs/
/api/stats/
/api/users/
/api/users/me/

## Golden response: /api/users/me/ without token
HTTP 401:
{"detail":"Authentication credentials were not provided."}
