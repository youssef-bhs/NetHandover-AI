"""
FastAPI Main Application.

Provides:
- Coverage prediction API
- RAG + LLM chat API
- Static file serving for plots
- CORS for React frontend
- Health checks

Run with: uvicorn app.main:app --reload --port 8000
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .config import settings
from .coverage_service import coverage_service
from .qos_service import qos_service

# Import routers
from .routers import chat, coverage, data, qos

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Network Coverage Assistant API",
    description="Coverage prediction API for telecom networks",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Add production frontend URL here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (plots)
plots_dir = settings.output_dir / "plots"
if plots_dir.exists():
    app.mount("/static/plots", StaticFiles(directory=str(plots_dir)), name="plots")
    logger.info(f"Mounted plots directory: {plots_dir}")

# Include routers
app.include_router(coverage.router)
app.include_router(chat.router)
app.include_router(data.router)
app.include_router(qos.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting application...")

    # 1. Load coverage model
    logger.info("Loading coverage model...")
    success = coverage_service.load_model()
    if success:
        logger.info("Coverage model loaded successfully")
    else:
        logger.warning("Coverage model not loaded. Check the pkl path and logs.")

    # 2. Load QoS model
    logger.info("Loading QoS model...")
    qos_loaded = qos_service.load_model()
    if qos_loaded:
        logger.info("QoS model loaded successfully")
    else:
        logger.warning("QoS model not loaded. Check the pkl path and logs.")

    # 3. Initialize RAG service (optional)
    try:
        from .rag_service import rag_service
        logger.info("Initializing RAG service...")
        if rag_service.initialize():
            logger.info("RAG service initialized")
        else:
            logger.warning("RAG service failed to initialize")
    except Exception as exc:
        logger.warning("RAG service unavailable: %s", exc)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirects to API docs."""
    return {"message": "Telecom Assistant API", "docs": "/docs", "health": "/api/health"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc) if settings.debug else None}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=settings.debug)
