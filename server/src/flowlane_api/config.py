"""Runtime configuration, read from environment variables (and a local `.env` file).

`DATABASE_URL` is any SQLAlchemy URL (https://docs.sqlalchemy.org/en/20/core/engines.html):

    sqlite:///./flowlane.sqlite3                     # file, relative to the working dir
    sqlite:///C:/data/flowlane.sqlite3               # file, absolute path
    sqlite://                                        # in-memory (tests; lost on exit)
    postgresql+psycopg://user:pass@host/flowlane     # later — needs the driver installed

The default is a SQLite file next to this package's project (`server/flowlane.sqlite3`),
so the dev server persists data no matter which directory it was started from.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{(SERVER_DIR / 'flowlane.sqlite3').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = DEFAULT_DATABASE_URL
    """SQLAlchemy connection URL — `DATABASE_URL` in the environment."""

    sql_echo: bool = False
    """Log every SQL statement — `SQL_ECHO=1` in the environment; handy while debugging."""


def load_settings() -> Settings:
    return Settings()
