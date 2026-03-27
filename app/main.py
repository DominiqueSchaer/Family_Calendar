from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from .routers import bookings, health
from .settings import settings

app = FastAPI(title=settings.app_name)
PUBLIC_DIR = Path(__file__).resolve().parents[1] / "public"
PUBLIC_INDEX = PUBLIC_DIR / "index.html"
PUBLIC_STATIC = PUBLIC_DIR / "static"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(bookings.router)

if PUBLIC_STATIC.exists():
    app.mount("/static", StaticFiles(directory=PUBLIC_STATIC), name="static")


@app.get("/", include_in_schema=False)
async def read_index() -> Response:
    if PUBLIC_INDEX.exists():
        return FileResponse(PUBLIC_INDEX)
    return RedirectResponse(url="/index.html", status_code=307)
