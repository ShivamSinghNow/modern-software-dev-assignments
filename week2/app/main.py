"""
Main FastAPI application with improved lifecycle management and error handling.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import init_db
from .exceptions import DatabaseError
from .routers import action_items, notes
from .schemas import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    try:
        # Initialize database
        init_db()
        print(f"✓ Database initialized at {settings.database_path}")
        print(f"✓ Application started: {settings.app_name} v{settings.app_version}")
    except DatabaseError as e:
        print(f"✗ Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    print("✓ Application shutting down")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Extract and manage action items from meeting notes and text",
    lifespan=lifespan,
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    Returns structured error responses.
    """
    errors = exc.errors()
    error_messages = [f"{err['loc']}: {err['msg']}" for err in errors]
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            detail="; ".join(error_messages),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ).model_dump(),
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(
    request: Request,
    exc: DatabaseError,
) -> JSONResponse:
    """
    Handle database errors.
    Returns structured error responses.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="DatabaseError",
            detail=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected errors.
    Returns structured error responses.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=type(exc).__name__,
            detail=str(exc) if settings.debug else "An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).model_dump(),
    )


# ============================================================================
# Routes
# ============================================================================

@app.get(
    "/",
    response_class=HTMLResponse,
    summary="Frontend homepage",
    description="Serves the frontend HTML page.",
)
def index() -> str:
    """
    Serve the frontend HTML page.
    
    Returns:
        HTML content of the frontend page
    """
    html_path = settings.frontend_dir / "index.html"
    if not html_path.exists():
        raise FileNotFoundError(f"Frontend file not found: {html_path}")
    return html_path.read_text(encoding="utf-8")


# Include routers
app.include_router(notes.router)
app.include_router(action_items.router)

# Mount static files
app.mount("/static", StaticFiles(directory=str(settings.frontend_dir)), name="static")


# ============================================================================
# Health Check
# ============================================================================

@app.get(
    "/health",
    summary="Health check",
    description="Returns the health status of the application.",
)
def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }
