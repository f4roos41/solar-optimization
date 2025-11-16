"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .routes import projects, analysis, auth, data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting up Solar Platform API...")
    # Initialize database connections, etc.
    yield
    logger.info("Shutting down Solar Platform API...")
    # Cleanup


# Create FastAPI application
app = FastAPI(
    title="Global Solar Energy Planning Platform API",
    description="RESTful API for solar site selection and analysis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(data.router, prefix="/data", tags=["Data Query"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Global Solar Energy Planning Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB check
        "queue": "connected"  # TODO: Add actual queue check
    }
