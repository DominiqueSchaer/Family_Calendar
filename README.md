# Family Calendar

Family Calendar couples a FastAPI backend with a lightweight, standalone HTMX + Tailwind frontend for managing reservations on a shared family resource. The frontend ships as a single HTML file that can be opened directly in the browser after compiling Tailwind.

This repo is wired for a simple Vercel deployment: FastAPI is exposed from `app/index.py` and re-exported from `api/index.py`, while static assets are served from `public/`.

## Project Layout

```
api/
  index.py             # Vercel API route entrypoint
app/
  index.py             # explicit Vercel FastAPI entrypoint
  main.py              # FastAPI application
  models.py
  schemas.py
  routers/
migrations/
  versions/
tests/
frontend-htmx/
  index.html           # source HTML for the static frontend
  static/
    styles.css         # Tailwind entrypoint
    output.css         # compiled stylesheet (generated)
public/
  index.html           # deployed static frontend
  static/
    output.css
```

## Backend (FastAPI)

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
4. Run the API locally:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Frontend (HTMX + Tailwind)

1. Build the stylesheet:
   ```bash
   cd frontend-htmx
   npm install       # first run only
   npm run build:css # or npm run dev:css for watch mode
   ```
2. Open `frontend-htmx/index.html` in your browser. The page will:
   - Use the site root as the backend base by default when deployed on Vercel.
   - Allow overriding the backend with `?apiBase=http://127.0.0.1:8000` or `localStorage.setItem('familyCalendar.apiBase', 'http://127.0.0.1:8000')` for local debugging.
   - Fetch live data from the FastAPI API if available.
   - Fall back to inlined mock data so you can explore the UI without the backend running.
3. Update `static/styles.css` and re-run `npm run build:css` whenever you change styles.

Because everything is either inlined or fetched via HTTPS at runtime, no dev server is required; refreshing `index.html` is enough to see changes after recompiling CSS.

## Quality Gates

Before opening a PR run:

- Backend: `pytest`, `ruff check .`, `black .`, `mypy .`
- Frontend: `npm run build:css` to ensure Tailwind compiles without errors.


## Vercel Deployment

1. Create a Vercel project pointed at this repository.
2. Set `DATABASE_URL` in the Vercel environment settings.
3. Deploy. Vercel serves the static frontend from `public/` and the FastAPI function from `api/index.py`.

The production dependency set is intentionally slimmed down for Vercel. Local-only tools such as `uvicorn` live in the `dev` extra, and the Python app now lives in a single `app/` package. Vercel is pointed at the FastAPI app explicitly through `[project.scripts]`.
The deployed frontend lives at `https://<your-project>.vercel.app/` and the API lives under `https://<your-project>.vercel.app/api/...`.
