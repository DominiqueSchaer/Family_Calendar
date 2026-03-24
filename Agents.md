# Repository Guidelines

## Project Structure & Module Organization
The repo is split into `backend/` for the FastAPI service, `frontend-htmx/` for templates and Tailwind assets, and supporting root configs such as `Dockerfile`, `Procfile`, and `README`. Within `backend/`, domain models live in `models.py`, request and response contracts in `schemas.py`, and feature routers under `routers/`. Database migrations stay in `migrations/`. Shared dependencies belong in `app/__init__.py` and settings modules. UI templates sit in `frontend-htmx/templates/`, while generated CSS is written to `frontend-htmx/static/output.css`. Tests reside in `backend/tests/` and mirror the feature hierarchy.

## Build, Test, and Development Commands
Run the API locally with `uvicorn app:app --reload --port 8000`. Apply schema changes using `alembic upgrade head` and create revisions with `alembic revision --autogenerate -m "short summary"`. Build Tailwind styles via `cd frontend-htmx; npm install; npm run dev:css`. Use `pytest` for the backend suite, and run `ruff check .`, `black .`, and `mypy .` before pushing.

## Coding Style & Naming Conventions
Python code is fully typed, four space indented, and formatted with Black. Enforce Ruff rule sets; any deviation needs an inline `# noqa` note. Prefer descriptive module and package names such as `bookings_router.py`. Keep money values as `Decimal` and centralize SQLAlchemy sessions through `get_db`. Jinja templates should lean on HTMX snippets and Tailwind utility classes, avoiding custom JavaScript when server driven interactions suffice.

## Testing Guidelines
Author tests with pytest, marking async cases with `pytest.mark.asyncio`. Name files `test_<feature>.py` and collect shared fixtures in `backend/tests/conftest.py`. Cover success and failure paths for routers, services, and data access. When introducing migrations, add a regression test that demonstrates the new schema behavior. Keep coverage meaningful; merges should wait on green test runs.

## Commit & Pull Request Guidelines
Write concise, imperative commit subjects such as `Add booking cancellation flow`. Group related changes per commit to keep diffs reviewable. Pull requests should describe intent, link tickets, note migrations or config updates, and include screenshots for frontend impact. Confirm lint, type checks, tests, and Tailwind build pass locally before requesting review.

## Environment & Configuration
Store secrets outside version control and load them via environment variables or `.env` files. Database URLs live in `settings.py`; override them per environment. Run `alembic upgrade head` after pulling to stay in sync. Use the provided Dockerfile to align local containers with deployment parity.
