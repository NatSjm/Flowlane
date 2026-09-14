"""HTTP layer — one router per openapi.yaml tag.

Routers only parse and serialize; the logic lives in `services/`."""

from flowlane_api.routers.boards import router as boards_router
from flowlane_api.routers.columns import router as columns_router
from flowlane_api.routers.tasks import router as tasks_router

__all__ = ["boards_router", "columns_router", "tasks_router"]
