"""Engine and session plumbing.

Everything here is dialect-agnostic except `_configure_sqlite`, which applies the two
things SQLite needs and other databases don't: allowing a pooled connection to be used
from FastAPI's worker threads, and turning foreign-key enforcement on (it's off by
default in SQLite; PostgreSQL & co. enforce constraints unconditionally).
"""

from typing import Any

from sqlalchemy import Engine, create_engine, event, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from flowlane_api.models import Base

SessionFactory = sessionmaker[Session]


def create_db_engine(database_url: str, *, echo: bool = False) -> Engine:
    url = make_url(database_url)
    kwargs: dict[str, Any] = {"echo": echo}
    if url.get_backend_name() == "sqlite":
        kwargs.update(_sqlite_engine_kwargs(is_memory=url.database in (None, "", ":memory:")))
    engine = create_engine(url, **kwargs)
    if url.get_backend_name() == "sqlite":
        _enable_sqlite_foreign_keys(engine)
    return engine


def create_session_factory(engine: Engine) -> SessionFactory:
    # Records stay usable after the request's commit (the routers serialize the
    # response from them), so don't expire attributes on commit.
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    """Create any missing tables. (Alembic migrations will take over once the schema
    starts evolving; `create_all` never alters existing tables.)"""
    Base.metadata.create_all(engine)


def _sqlite_engine_kwargs(*, is_memory: bool) -> dict[str, Any]:
    # FastAPI runs sync endpoints/dependencies in a thread pool, so a pooled
    # connection legitimately crosses threads between requests.
    kwargs: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
    if is_memory:
        # An in-memory SQLite database lives and dies with its connection; share one
        # connection process-wide so every session sees the same database.
        kwargs["poolclass"] = StaticPool
    return kwargs


def _enable_sqlite_foreign_keys(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
