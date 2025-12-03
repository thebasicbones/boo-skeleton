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
from fastapi.staticfiles import StaticFiles

from app.database_factory import close_database, init_database
from app.error_handlers import register_exception_handlers
from app.routers import resources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info("Starting up application...")
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


# Create FastAPI application instance
app = FastAPI(
    title="FastAPI CRUD Backend",
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
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(resources.router)

# Mount static files directory for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - returns API information.
    """
    return {
        "message": "FastAPI CRUD Backend API",
        "version": "1.0.0",
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

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info",
    )
