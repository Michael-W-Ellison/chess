"""
Tamagotchi Chatbot Backend - Main Application

FastAPI application for local chatbot with personality and memory.
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from utils.config import settings
from utils.logging_config import setup_logging
from database.database import init_db, close_db
from services.llm_service import llm_service
from services.report_scheduler import report_scheduler

# Import routes
from routes import conversation, personality, profile, parent

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI app
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Tamagotchi Chatbot Backend...")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Load LLM model with optimizations from settings
    logger.info(f"Loading LLM model from {settings.MODEL_PATH}")

    # Log cache configuration
    if settings.ENABLE_RESPONSE_CACHE:
        logger.info(f"Response caching enabled: TTL={settings.CACHE_TTL_SECONDS}s, Max={settings.CACHE_MAX_SIZE}")
    else:
        logger.info("Response caching disabled")

    # Configure loading based on settings
    use_mmap = settings.MODEL_USE_MMAP
    blocking = not settings.MODEL_BACKGROUND_LOAD
    lazy_load = settings.MODEL_LAZY_LOAD

    if lazy_load:
        logger.info("Lazy loading enabled - model will load on first chat request")
    else:
        logger.info(f"Loading model: mmap={use_mmap}, background={settings.MODEL_BACKGROUND_LOAD}")

        # Start model loading
        model_loading_started = llm_service.load_model(blocking=blocking, use_mmap=use_mmap)

        if model_loading_started:
            if settings.MODEL_BACKGROUND_LOAD:
                logger.info("✓ LLM model loading started in background")
                logger.info("  App is ready - model will finish loading shortly")
                logger.info("  First chat request will wait for model if needed")
            else:
                logger.info("✓ LLM model loaded successfully")
        else:
            logger.warning("⚠ LLM model loading failed to start - chatbot functionality will be limited")
            logger.warning("  Download a model with: ./scripts/download_model.sh")

    # Start report scheduler
    if settings.ENABLE_WEEKLY_REPORTS and settings.ENABLE_PARENT_NOTIFICATIONS:
        logger.info("Starting automated report scheduler...")
        report_scheduler.start()
        logger.info("✓ Report scheduler started - will check for due reports every hour")
    else:
        logger.info("Report scheduler disabled (ENABLE_WEEKLY_REPORTS or ENABLE_PARENT_NOTIFICATIONS is False)")

    logger.info(f"Backend ready at http://{settings.HOST}:{settings.PORT}")

    yield

    # Shutdown
    logger.info("Shutting down Tamagotchi Chatbot Backend...")

    # Stop report scheduler
    report_scheduler.stop()
    logger.info("Report scheduler stopped")

    # Unload LLM model
    llm_service.unload_model()

    close_db()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Tamagotchi Chatbot API",
    description="Local chatbot companion with evolving personality and memory",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS Middleware - allow Electron frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Alternative port
        "file://",                # Electron production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error" if not settings.DEBUG else str(exc),
        },
    )


# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Tamagotchi Chatbot API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with cache statistics"""
    return {
        "status": "healthy",
        "database": "connected",
        "llm": "loaded" if llm_service.is_loaded else "not loaded",
        "model_info": llm_service.get_model_info(),
    }


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all LLM response caches"""
    stats = llm_service.clear_cache()
    logger.info("Cache cleared via API")
    return {
        "success": True,
        "message": "Cache cleared successfully",
        "previous_stats": stats,
    }


@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return {
        "success": True,
        "cache_stats": llm_service.get_cache_stats(),
    }


# Include routers
app.include_router(conversation.router, prefix="/api", tags=["conversation"])
app.include_router(personality.router, prefix="/api", tags=["personality"])
app.include_router(profile.router, prefix="/api", tags=["profile"])
app.include_router(parent.router, prefix="/api/parent", tags=["parent"])


# Development server runner
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
