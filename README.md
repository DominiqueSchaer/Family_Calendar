# Bookly

Bookly couples a FastAPI backend with a lightweight, standalone HTMX + Tailwind frontend for managing reservations on a shared resource. The frontend ships as a single HTML file that can be opened directly in the browser after compiling Tailwind.

This repo is wired for a simple split deployment: FastAPI runs on Vercel as a standard serverless function, while the HTMX frontend stays a standalone static site.

## Project Layout

```
app.py                 # Vercel FastAPI entrypoint
backend/
  app/
    main.py
    models.py
    schemas.py
    routers/
  migrations/
frontend-htmx/
  index.html           # fully rendered calendar UI with inline logic
  static/
    styles.css         # Tailwind entrypoint
    output.css         # compiled stylesheet (generated)
scripts/
  ...                  # optional local helpers
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
   uvicorn backend.app.main:app --reload --port 8000
   ```

## Frontend (HTMX + Tailwind)

1. Build the stylesheet:
   ```bash
   cd frontend-htmx
   npm install       # first run only
   npm run build:css # or npm run dev:css for watch mode
   ```
2. Open `frontend-htmx/index.html` in your browser. The page will:
   - Read the backend base URL from `<meta name="api-base">` (defaults to `https://bookly-v.vercel.app`).
   - Allow overriding the backend with `?apiBase=http://localhost:8000` or `localStorage.setItem('bookly.apiBase', 'http://localhost:8000')`.
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
3. Deploy. Vercel will detect `app.py` as the Python serverless entrypoint.

The deployed API base will be `https://<your-project>.vercel.app`. Because the frontend is now fully static, it can live on GitHub Pages, any static host, or be opened locally while talking to the Vercel backend.
