# courses-api

Django 5 / DRF API for the course catalogue, cart, orders, payments, enrollments and
Practice Labs.

## Local setup

Requirements: Docker with Compose v2. Lab execution additionally requires privileged
Linux containers.

1. Create the local environment file and fill in the SSO values:

   ```sh
   cp .env.example .env.local
   ```

2. Start the API and database:

   ```sh
   docker compose up -d
   ```

   The API is available at `http://localhost:8080`.

3. Start the local Piston code-execution engine (required for Practice Labs):

   ```sh
   docker compose -f infrastructure/piston/docker-compose.yml up -d
   sh infrastructure/piston/install-runtimes.sh
   ```

   See [`infrastructure/piston/README.md`](infrastructure/piston/README.md) for ports,
   runtime versions and troubleshooting.

To stop the API stack:

```sh
docker compose down
```

## Tests

```sh
docker compose run --rm app sh -c "python manage.py test"
docker compose run --rm app sh -c "python manage.py test lab"
docker compose run --rm app sh -c "python manage.py test courses"
```

## Practice Labs

Lab endpoints live under `/api/lab/`. Execution is forwarded to Piston at `PISTON_URL`;
without a reachable Piston instance, the execute endpoint returns `502`.

The local Piston stack is self-contained and does not require the Digital-Readiness-Lab
repository. The required runtimes are Python `3.12.0`, PHP `8.2.3` and TypeScript `5.0.3`.

## Deployment

Pushing to `main` runs the Cloud Run deployment workflow. Production Piston is not
managed by Cloud Run: provide a private Piston endpoint through `PISTON_URL` in the
deployment environment.
