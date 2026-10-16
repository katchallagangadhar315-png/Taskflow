from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.db.session import engine, Base
import app.models  # Ensures models are imported so Base.metadata knows about them
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router

# Base project path to locate the frontend folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Initialize FastAPI application with informative metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend REST API for TaskFlow - Smart Task Management System",
    version="1.0.0",
    docs_url="/docs",      # Interactive Swagger UI documentation
    redoc_url="/redoc"    # Alternative ReDoc documentation
)

# Automatically create database tables in MySQL if they do not exist
Base.metadata.create_all(bind=engine)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows our frontend (HTML/JS) running on any port or file:// protocol
# to communicate with the FastAPI backend without browser blocking.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # In development, accept all origins
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],            # Allow all HTTP headers (Authorization, Content-Type, etc.)
)

# Register API Routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")

from fastapi.responses import FileResponse

# Mount static asset directories so relative paths work from root / as well as /frontend
if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/", tags=["Frontend"], response_class=FileResponse, summary="Serve TaskFlow Frontend Homepage")
async def root():
    """
    Serves the actual TaskFlow frontend homepage (index.html).
    Contains full registration capabilities and links to Sign In.
    """
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "TaskFlow frontend not found", "documentation": "/docs"}


@app.get("/login.html", tags=["Frontend"], include_in_schema=False)
@app.get("/login", tags=["Frontend"], include_in_schema=False)
async def serve_login():
    """Serves the login page."""
    login_file = FRONTEND_DIR / "login.html"
    if login_file.exists():
        return FileResponse(login_file)
    return {"detail": "login.html not found"}


@app.get("/dashboard.html", tags=["Frontend"], include_in_schema=False)
@app.get("/dashboard", tags=["Frontend"], include_in_schema=False)
async def serve_dashboard():
    """Serves the personal dashboard page."""
    dashboard_file = FRONTEND_DIR / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file)
    return {"detail": "dashboard.html not found"}


@app.get("/index.html", tags=["Frontend"], include_in_schema=False)
@app.get("/register", tags=["Frontend"], include_in_schema=False)
async def serve_register():
    """Serves the registration page."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"detail": "index.html not found"}


@app.get("/api", tags=["General"])
async def api_info():
    """
    Provides API status and links to interactive documentation.
    """
    return {
        "message": "Welcome to TaskFlow API!",
        "project": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint:
    Used by clients and monitoring tools to confirm service health and environment.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
