# Load libraries
import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse, Response

from backend.api.auth import router as auth_router
from backend.api.health import router as health_router
from backend.api.middleware import SetupGuardMiddleware
from backend.api.notifications import router as notifications_router
from backend.api.settings import router as settings_router
from backend.api.setup import router as setup_router
from backend.core.config import settings, validate_secrets
from backend.core.database import init_db
from backend.core.logging_config import setup_logging
from backend.core.security import limiter


# Configures startup and shutdown lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_secrets()
    setup_logging()
    await init_db()
    yield


app = FastAPI(
    title="BibliothecaFabulae",
    description="Self-hosted personal fanfiction archive and reader",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.add_middleware(SetupGuardMiddleware)


_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_ALLOWED_ORIGINS = {urlparse(o).netloc or urlparse(o).path for o in settings.CORS_ORIGINS}


@app.middleware("http")
async def csrf_origin_check(request: Request, call_next) -> Response:
    if (
        request.method not in _SAFE_METHODS
        and request.url.path.startswith("/api")
    ):
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        if origin:
            origin_host = urlparse(origin).netloc
        elif referer:
            origin_host = urlparse(referer).netloc
        else:
            origin_host = None

        if origin_host and origin_host not in _ALLOWED_ORIGINS:
            return JSONResponse(
                status_code=403,
                content={"detail": "Cross-origin request blocked"},
            )

    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    if settings.ENVIRONMENT != "development":
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )

    return response


# Route registration
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(setup_router)
app.include_router(settings_router)
app.include_router(notifications_router)

# SPA static file serving
frontend_build = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")

if os.path.isdir(frontend_build):
    _frontend_base = Path(frontend_build).resolve()

    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_build, "assets")), name="assets")

    # Serves the SPA for all unmatched routes
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        file_path = (_frontend_base / full_path).resolve()

        if not str(file_path).startswith(str(_frontend_base)):
            return FileResponse(_frontend_base / "index.html")

        if full_path and file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(_frontend_base / "index.html")
