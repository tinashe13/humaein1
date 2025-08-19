from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from .config import Settings, get_settings
from .logging import configure_logging
from .db import create_indexes
from .metrics import instrument_app
from .routers import datasets, reclassify, pipeline, metrics as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # Make startup resilient even if Mongo is not yet reachable
    try:
        create_indexes()
    except Exception as exc:  # noqa: BLE001
        import logging
        logging.getLogger(__name__).warning("MongoDB not reachable on startup: %s", exc)
    # Ensure artifacts directory exists to avoid StaticFiles mount errors on Windows reloads
    try:
        from .config import get_settings as _gs
        import os as _os
        _os.makedirs(_gs().artifacts_dir, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        import logging
        logging.getLogger(__name__).warning("Could not ensure artifacts dir exists: %s", exc)
    yield


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    app = FastAPI(
        title="Claim Resubmission Ingestion Pipeline",
        version="0.1.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        redirect_slashes=False,  # Prevent 307 redirects
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
        ],
        expose_headers=["*"],
    )

    app.include_router(datasets.router, prefix="/api")
    app.include_router(reclassify.router, prefix="/api")
    app.include_router(pipeline.router, prefix="/api")
    app.include_router(metrics_router.router)

    # Serve artifacts statically for downloads
    from fastapi.staticfiles import StaticFiles
    from .config import get_settings as _gs
    # check_dir=False prevents crash if dir disappears during reload; we ensure it in lifespan
    app.mount("/artifacts", StaticFiles(directory=_gs().artifacts_dir, check_dir=False), name="artifacts")

    instrument_app(app)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=bool(int(os.getenv("RELOAD", "1"))),
        log_config=None,  # structlog configured separately
    )


