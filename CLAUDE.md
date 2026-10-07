# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Python Package Management with uv
Use `uv` exclusively. Never use pip, poetry, or conda directly.
- Install/Remove: `uv add <pkg>` / `uv remove <pkg>`
- Sync/Lock: `uv sync` / `uv lock`
- Execution: `uv run <command>` (e.g., `uv run python`, `uv run pytest`)

## Commands

Backend (FastAPI, run from repo root):
- Dev server: `uv run fastapi dev` (serves `app/main.py` on http://localhost:8000; docs at `/docs`)
- All tests: `uv run pytest`
- One file / one test: `uv run pytest tests/test_galleries.py` / `uv run pytest tests/test_galleries.py::test_default_gallery_is_created`

Frontend (React 19 + Vite, run from `frontend/`):
- `npm run dev` (Vite on :5173), `npm run build`, `npm run lint` (oxlint)
- No frontend test suite exists.

Static public site (`static/`, plain HTML/CSS, independent of the React app and API):
- Contact form handler is `static/cgi-bin/contact.py` (stdlib-only CGI, sends via Gmail SMTP); tested by `tests/test_contact_form.py`.
- Production runs via `docker compose up -d --build` from the repo root: `caddy` (HTTPS, the only service publishing ports, config in `deploy/Caddyfile`) in front of `static-site` (Apache, `static/Dockerfile`). Needs git-ignored `deploy/site.env` and `deploy/contact.ini`; see `deploy/README.md`.
- Future services join the compose `web` network without published ports and get a route in `deploy/Caddyfile`. Don't put compose/site variables in the root `.env`: the backend's `Settings` rejects unknown keys.

## Configuration

- Backend reads `.env` at repo root via `pydantic-settings` (`app/config/settings.py`): `DATABASE_URL` (defaults to SQLite `./church-alliance.db`), `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `CLOUDINARY_*`.
- Frontend reads `frontend/.env`: `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`.
- CORS origins are hard-coded in `app/main.py`; add new frontend hosts there. The `X-Total-Count` header is exposed for paginated lists.

## Architecture

**Backend layering.** Each domain (user, event, certification, asset, gallery, article) has two halves:
- `app/db/<domain>/` — `models.py` (SQLAlchemy), `schemas.py` (Pydantic), `crud.py` (all DB access); the package `__init__` re-exports these.
- `app/api/v1/<domain>/routes.py` — the `APIRouter`, exported from its `__init__` and mounted under `/api/v1` in `app/main.py`. The galleries package exports two routers (`router` for `/galleries`, `pictures_router` for `/pictures`).

`app/db/models.py`, `app/db/crud.py`, `app/db/schemas.py` are backwards-compat re-export shims; import from the domain packages instead. A new model must be imported somewhere reachable from `app/db/__init__.py` so `Base.metadata.create_all` sees it.

**Schema migrations.** There is no Alembic. `create_tables()` in `app/db/__init__.py` runs on app startup (lifespan): it calls `create_all`, then hand-written `_migrate_*` functions that `ALTER TABLE ADD COLUMN` for columns missing from older databases, then ensures the "Default" gallery exists. When adding a column to an existing table, add a matching `_migrate_*` step.

**Auth.** Supabase handles signup/login on the frontend; the backend never issues tokens. In `app/api/v1/auth/dependencies.py`, `decode_token` verifies the Supabase bearer JWT with PyJWT (ES256 via the Supabase JWKS endpoint, using a cached `PyJWKClient`; otherwise HS256 with `SUPABASE_JWT_SECRET`). Only `POST /api/v1/auth/sync-user` (via `sync_current_user`) creates or updates the local `User` row from token claims, keyed by `auth_id` (the JWT `sub`); the frontend calls it after login. Every other route uses `get_current_user`, which is read-only and returns 401 for a valid token whose user hasn't been synced.

**Roles.** `UserRole` = `applicant` (default for new users) < `member` < `coordinator` < `administrator`. Authorization helpers live in `dependencies.py`; use them rather than inline `current_user.role` checks:
- Route-level dependencies: `require_manager(detail)` (coordinator/admin), `require_confirmed(detail)` (non-applicant), or the general `allow_roles(...)` / `disallowed_roles(...)`. Pass a `detail` — the frontend shows it to the user.
- Resource ownership (needs the loaded row, so called in the route body): `ensure_owner_or_role(user, owner_id, detail, roles=MANAGER_ROLES)` raises 403; `is_owner_or_role` / `is_manager` return bools.
- `get_optional_current_user` is for public endpoints that mask data (e.g. surnames) for anonymous users and applicants.

The frontend mirrors these rules to decide which sections are visible (`frontend/src/App.jsx`), but the backend is the authority.

**Picture storage.** Images live in Cloudinary; `app/db/` never talks to it. Three layers:
- `app/storage/images.py` — `CloudinaryImageStorage`, the only Cloudinary client, injected via the `get_image_storage` dependency.
- `app/services/pictures.py` — orders storage vs. database steps so that on failure we leave an orphaned image rather than a `Picture` pointing at a missing one.
- `app/db/gallery/crud.py` — database only; delete functions return the removed `cloudinary_public_id`s for the service to clean up.

Uploads go browser → Cloudinary directly: `POST /pictures/upload-signature` returns signed form fields (folder, `pending` tag, allowed formats); the browser posts the file to Cloudinary, then sends Cloudinary's signed response (`public_id`, `version`, `signature`) to `POST /pictures`, which verifies it, removes the `pending` tag and saves the row. Abandoned uploads keep the tag and are purged by `uv run python -m app.storage.cleanup` (meant to run on a schedule). Image deletes run as background tasks after the row is committed; failures are logged, not raised.

**Frontend.** Single-page app without a router: `App.jsx` owns Supabase session, role, and `activeSection` state; `components/MainContent.jsx` switches on `activeSection` to render one `*Tool.jsx` component, passing `apiBaseUrl`, the auth token, `userRole`, and `backendUserId` as props. Components call the API directly with `fetch`. Rich text is edited with Slate; HTML event descriptions are rendered via `dangerouslySetInnerHTML` wrapped in `DOMPurify.sanitize`.

## Tests

`tests/conftest.py` uses an in-memory SQLite engine, overrides `get_db` with a per-test session wrapped in a rolled-back transaction, and monkeypatches `settings.supabase_jwt_secret` to a test value. Tests create a `User` with the desired role via `create_user` (protected routes won't auto-create it), then mint an HS256 token with PyJWT's `jwt.encode` whose `sub` matches that user's `auth_id` (see `make_token` helpers in the test files). The `client` fixture overrides `get_image_storage` with `FakeImageStorage` (the `image_storage` fixture), so tests never reach Cloudinary; use `image_storage.signature_for(public_id, version)` to build a valid upload confirmation. `tests/test_image_storage.py` checks the real Cloudinary signing with the network stubbed. Note `create_user` makes the first user in an empty database an administrator.
