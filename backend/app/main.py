from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .routers import bookings, health
from .settings import settings

ROOT_DIR = Path(__file__).resolve().parents[2]
PUBLIC_INDEX = ROOT_DIR / "public" / "index.html"

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(bookings.router)


@app.get("/", include_in_schema=False)
async def read_root() -> FileResponse:
    return FileResponse(PUBLIC_INDEX)
