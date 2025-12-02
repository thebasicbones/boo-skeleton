"""Main FastAPI application entry point"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import resources
from app.error_handlers import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup: Initialize database
    logger.info("Starting application - initializing database")
    await init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown: cleanup if needed
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title="FastAPI CRUD Backend",
    description="RESTful API with CRUD operations and topological sort search",
    version="1.0.0",
    lifespan=lifespan
)

# Register global exception handlers
register_exception_handlers(app)

# Configure CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(resources.router)

# Mount static files directory for frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
