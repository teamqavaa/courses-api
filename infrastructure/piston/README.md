# Local Piston for courses-api

`courses-api` sends lab execution requests to a Piston-compatible API at `PISTON_URL`.
This directory provides a self-contained local stack, so another developer does not need
the Digital-Readiness-Lab infrastructure.

## Prerequisites

- Docker Engine or Docker Desktop with Compose v2
- A Docker daemon that supports privileged Linux containers
- `sh` and `curl` on the host
- Internet access the first time the image and runtimes are installed

## Start Piston

From the `courses-api` repository root:

```sh
docker compose -f infrastructure/piston/docker-compose.yml up -d
```

The API is exposed on `http://localhost:2000`. Runtime data and installed packages are
stored in named Docker volumes and survive container recreation.

If another Piston instance already uses port `2000` (for example the DRL stack), select
another host port:

```sh
PISTON_HOST_PORT=2002 docker compose -f infrastructure/piston/docker-compose.yml up -d
PISTON_URL=http://localhost:2002 sh infrastructure/piston/install-runtimes.sh
```

## Install the required runtimes

The Piston image does not include the lab runtimes by default. Install the exact versions
used by `contents-lab/lib/lab/languages.ts`:

```sh
sh infrastructure/piston/install-runtimes.sh
```

The script waits for Piston, skips runtimes that are already installed, and installs:

- Python `3.12.0`
- PHP `8.2.3`
- TypeScript `5.0.3`

Use a different endpoint with `PISTON_URL`:

```sh
PISTON_URL=http://localhost:2002 sh infrastructure/piston/install-runtimes.sh
```

## Configure courses-api

`courses-api` runs in Docker Compose, so use the Docker host address in `.env.local`:

```env
PISTON_URL=http://host.docker.internal:2000
```

If Django runs outside Docker, use `PISTON_URL=http://localhost:2000` instead.

When using a non-default host port, use the matching value:

```env
PISTON_URL=http://host.docker.internal:2002
```

## Verify

Check the installed runtimes:

```sh
curl -fsS http://localhost:2000/api/v2/runtimes
```

Run a small Python job:

```sh
curl -fsS -X POST http://localhost:2000/api/v2/execute \
  -H "Content-Type: application/json" \
  -d '{"language":"python","version":"3.12.0","files":[{"name":"main.py","content":"print(6 * 7)"}]}'
```

The response should contain `"stdout":"42\n"`.

## Stop or reset

Stop the container while keeping installed runtimes:

```sh
docker compose -f infrastructure/piston/docker-compose.yml down
```

Delete the container and all installed runtimes:

```sh
docker compose -f infrastructure/piston/docker-compose.yml down -v
```

## Notes

- This stack omits the DRL nginx CORS proxy because `courses-api` calls Piston
  server-to-server. A browser calling Piston directly would need its own CORS layer.
- The container executes untrusted code and runs privileged. Keep it local; never expose
  it publicly.
- `PISTON_DISABLE_NETWORKING=false` is intentional for local development. Set it to
  `true` in a production deployment unless exercises require network access.
- Production Piston must run outside Cloud Run on private infrastructure and be reachable
  through `PISTON_URL`. This Compose file is for local development only.
