# Fluffy

## Backend and database

- `app.main:app` is the FastAPI entrypoint. Register endpoint routers in `app/api/v1/__init__.py`; `app/api/__init__.py` adds `/v1`. `app/dependencies.py` wires services to a request-scoped SQLAlchemy session through `app/repository/uow.py`.
- Run host Python and Alembic commands from the repo root: `app/core/config.py` loads `.env` and `config.yaml` relative to the working directory at import time. Use `postgresql+asyncpg://` for `POSTGRES_URL`; Compose uses service hostnames, while host commands need published ports. Set a numeric `SMTP_PORT` or omit it (the blank example value fails validation).
- `docker compose --profile prod up --build -d` starts the API on `:8000` and the nginx-served SPA on `:8080`. API startup pings Redis. Once Postgres is ready, run `docker compose --profile prod exec api alembic upgrade head`; startup does not apply migrations.
- ORM models live in `app/model/`. Ensure new models are imported by `migrations/env.py` before running `alembic revision --autogenerate -m "..."` against an up-to-date dev database. Review the generated revision under `migrations/versions/` and add a new revision for schema changes. The current migration chain does not create the ORM's `friendships` table.

## Backend tests

- CI starts services with `docker compose --profile test up -d --build`, then runs `docker compose --profile test exec testapi pytest -v`. For a focused run, replace `pytest -v` with `pytest tests/integration/database/test_db_session.py` or `pytest -m unit`.
- Even `-m unit` requires a disposable Postgres DB: `tests/conftest.py` reads `POSTGRES_URL` from the process environment (Compose maps `TEST_POSTGRES_URL` to it), requires `test` in the database name, and creates/drops all ORM tables once per session. Host pytest must export `POSTGRES_URL` explicitly; Compose publishes test Postgres on `:5433`. The suite builds its schema from models, so passing tests do not verify Alembic migrations.
- The `client` fixture sends requests in-process via `ASGITransport` without running FastAPI lifespan. It overrides `get_db` with a savepoint-backed session so service commits still roll back after each test.

## Frontend

- In `frontend/`, use Node `^22.18.0 || >=24.12.0`, `npm ci`, and `npm run dev`; verify changes with `npm run build`. Vite proxies same-origin `/v1` HTTP and WebSocket traffic to `localhost:8000`. The nginx image builds and serves `frontend/dist` and proxies `/v1/` to `api:8000`; `pages/` is a separate static GitHub Pages site.
- `frontend/src/main.js` wires Vue, Pinia, and the router. Put feature routes in `src/modules/<feature>/routes.js` and register new modules in `src/app/router/index.js` (paths relative to `frontend/`). Use `@/shared/api/client` for HTTP so token refresh and session expiry go through the shared flow.
- For auth, cache, or WebSocket changes, check logout followed by login as a different account. Clear account-specific state on session changes and key persisted caches by user; see `frontend/readme.md`.
