"""FastAPI dependency wiring.

`get_store` is the single seam for persistence: one SQLAlchemy session per request,
committed when the endpoint returns normally and rolled back when it raises. The
session factory comes from `app.state` (set up in `main.create_app`'s lifespan), so
tests get a different database simply by building the app with different settings.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request

from flowlane_api.db import SessionFactory
from flowlane_api.repositories import SqlStore, Store
from flowlane_api.services import BoardService, ColumnService, TaskService


def get_store(request: Request) -> Iterator[Store]:
    session_factory: SessionFactory = request.app.state.session_factory
    with session_factory() as session:
        yield SqlStore(session)
        # Only reached when the endpoint (and every dependency) succeeded — an
        # exception propagates through the yield and `Session.__exit__` rolls back.
        session.commit()


# `scope="function"` runs the commit *before* the response is sent (the default
# "request" scope would run it after, so a client could read back stale data).
StoreDep = Annotated[Store, Depends(get_store, scope="function")]


def get_board_service(store: StoreDep) -> BoardService:
    return BoardService(store)


def get_column_service(store: StoreDep) -> ColumnService:
    return ColumnService(store)


def get_task_service(store: StoreDep) -> TaskService:
    return TaskService(store)


BoardServiceDep = Annotated[BoardService, Depends(get_board_service)]
ColumnServiceDep = Annotated[ColumnService, Depends(get_column_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
