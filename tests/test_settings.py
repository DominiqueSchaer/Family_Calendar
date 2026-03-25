from app.settings import Settings


def test_normalize_postgres_url() -> None:
    settings = Settings(DATABASE_URL="postgres://user:pass@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


def test_normalize_postgresql_url() -> None:
    settings = Settings(DATABASE_URL="postgresql://user:pass@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


def test_keep_asyncpg_url() -> None:
    settings = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://user:pass@host:5432/db"
