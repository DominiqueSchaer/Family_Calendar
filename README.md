# Bookly

Bookly couples a FastAPI backend with a lightweight, standalone HTMX + Tailwind frontend for managing reservations on a shared resource. The frontend ships as a single HTML file that can be opened directly in the browser after compiling Tailwind.

This repo is wired for a simple split deployment: FastAPI runs on Vercel from the root `app.py` entrypoint, while static assets are served from `public/`.

## Project Layout

```
app.py                 # Vercel and local FastAPI entrypoint
backend/
  app/
    main.py
    models.py
    schemas.py
    routers/
  migrations/
frontend-htmx/
  index.html           # source HTML for the static frontend
  index_approval.html
  static/
    styles.css         # Tailwind entrypoint
    output.css         # compiled stylesheet (generated)
public/
  index.html           # deployed static frontend
  index_approval.html
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
4. Run the API:
   ```bash
   uvicorn app:app --reload --port 8000
   ```

## Frontend (HTMX + Tailwind)

1. Build the stylesheet:
   ```bash
   cd frontend-htmx
   npm install       # first run only
   npm run build:css # or npm run dev:css for watch mode
   ```
2. Open `frontend-htmx/index.html` in your browser. The page will:
   - Use same-origin API routes by default when deployed on Vercel.
   - Allow overriding the backend with `?apiBase=http://127.0.0.1:8000` or `localStorage.setItem('bookly.apiBase', 'http://127.0.0.1:8000')` for local debugging.
   - Fetch live data from the FastAPI API if available.
   - Fall back to inlined mock data so you can explore the UI without the backend running.
3. Update `static/styles.css` and re-run `npm run build:css` whenever you change styles.

Because everything is either inlined or fetched via HTTPS at runtime, no dev server is required—refreshing `index.html` is enough to see changes after recompiling CSS.

## Quality Gates

Before opening a PR run:

- Backend: `pytest`, `ruff check .`, `black .`, `mypy .`
- Frontend: `npm run build:css` to ensure Tailwind compiles without errors.


## Vercel Deployment

1. Create a Vercel project pointed at this repository.
2. Set `DATABASE_URL` in the Vercel environment settings.
3. Deploy. Vercel can detect the root `app.py` entrypoint without additional routing configuration.

The deployed API and frontend share the same origin at `https://<your-project>.vercel.app`, so the frontend can call `/health`, `/bookings`, and the other FastAPI routes directly.
