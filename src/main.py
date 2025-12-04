"""
FastAPI CRUD Backend Application Entry Point

This module initializes the FastAPI application with all necessary
configurations, middleware, routers, and error handlers.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database_factory import close_database, init_database
from app.error_handlers import register_exception_handlers
from app.observability import init_observability, shutdown_observability
from app.observability.config import ObservabilitySettings
from app.routers import resources
from config.settings import get_settings

# Load settings
settings = get_settings()
observability_settings = ObservabilitySettings.from_settings(settings)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)
logger.info(f"Starting application in {settings.environment} environment")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize observability and database
    logger.info("Starting up application...")

    # Initialize OpenTelemetry observability
    try:
        init_observability(observability_settings)
        logger.info("Observability initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize observability: {e}", exc_info=True)
        # Continue without observability

    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_database()

    # Shutdown observability
    try:
        shutdown_observability()
        logger.info("Observability shutdown successfully")
    except Exception as e:
        logger.warning(f"Error during observability shutdown: {e}", exc_info=True)


# Create FastAPI application instance
app = FastAPI(
    title=settings.app_title,
    description="""
    A RESTful API backend with CRUD operations and topological sorting capabilities.

    ## Features

    * **Create** resources with dependencies
    * **Read** individual resources or list all resources
    * **Update** existing resources and their dependencies
    * **Delete** resources with optional cascade deletion
    * **Search** resources with topological sorting based on dependencies

    ## Topological Sorting

    The search endpoint returns resources ordered by their dependencies,
    ensuring that dependencies always appear before their dependents.
    This is useful for processing resources in the correct order.

    ## Dependency Management

    Resources can depend on other resources, forming a directed acyclic graph (DAG).
    The system automatically detects and prevents circular dependencies.
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.debug,
)

# Configure CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(resources.router)

# Mount static files directory for frontend
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - returns API information.
    """
    return {
        "message": "FastAPI CRUD Backend API",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint - returns application status.
    """
    return {"status": "healthy", "service": "fastapi-crud-backend"}


if __name__ == "__main__":
    import uvicorn

    # Run the application with settings from configuration
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
