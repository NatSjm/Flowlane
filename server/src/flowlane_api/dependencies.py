"""FastAPI dependency wiring.

`get_store` is the single seam for persistence: the app holds one process-wide
`InMemoryStore` today; tests override this dependency with a fresh store per test,
and the SQL implementation will swap in a session-scoped store here.
"""

from typing import Annotated

from fastapi import Depends, Request

from flowlane_api.repositories import Store
from flowlane_api.services import BoardService, ColumnService, TaskService


def get_store(request: Request) -> Store:
    store: Store = request.app.state.store
    return store


StoreDep = Annotated[Store, Depends(get_store)]


def get_board_service(store: StoreDep) -> BoardService:
    return BoardService(store)


def get_column_service(store: StoreDep) -> ColumnService:
    return ColumnService(store)


def get_task_service(store: StoreDep) -> TaskService:
    return TaskService(store)


BoardServiceDep = Annotated[BoardService, Depends(get_board_service)]
ColumnServiceDep = Annotated[ColumnService, Depends(get_column_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
