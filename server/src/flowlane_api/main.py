"""Flowlane API — FastAPI implementation of ../../openapi.yaml.

Run locally with `uv run fastapi dev src/flowlane_api/main.py` (see server/README.md).
"""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from flowlane_api.errors import register_error_handlers
from flowlane_api.repositories.memory import InMemoryStore
from flowlane_api.routers import boards_router, columns_router, tasks_router

# openapi.yaml: `servers: [{url: /api}]` — the frontend fetches relative to this prefix.
API_PREFIX = "/api"

# The Vite dev server origin (frontend/README.md). Same-origin in production, so this
# only matters for local development.
DEV_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Flowlane API",
        version="0.1.0",
        description=(
            "Backend for the Flowlane Kanban board. Contract: openapi.yaml at the repo root."
        ),
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
    )
    # The mock database. Process-local and lost on restart; swapped for a real
    # database later via `dependencies.get_store`.
    app.state.store = InMemoryStore()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEV_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(boards_router)
    api.include_router(columns_router)
    api.include_router(tasks_router)

    @api.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api)
    return app


app = create_app()
