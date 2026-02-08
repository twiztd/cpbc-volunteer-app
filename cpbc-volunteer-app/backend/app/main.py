import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import engine, Base, SessionLocal
from .models import CustomMinistryTag
from .schemas import MINISTRY_CATEGORIES
from .routes import volunteers, admin

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Starting CPBC Volunteer App API")
    # Create database tables (for development - use Alembic migrations in production)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Load custom ministry tags from DB into in-memory MINISTRY_CATEGORIES
    db = SessionLocal()
    try:
        custom_tags = db.query(CustomMinistryTag).all()
        for tag in custom_tags:
            if tag.category in MINISTRY_CATEGORIES:
                if tag.ministry_area not in MINISTRY_CATEGORIES[tag.category]:
                    MINISTRY_CATEGORIES[tag.category].append(tag.ministry_area)
        if custom_tags:
            logger.info(f"Loaded {len(custom_tags)} custom ministry tag(s)")
    finally:
        db.close()

    yield
    logger.info("Shutting down CPBC Volunteer App API")


app = FastAPI(
    title="CPBC Volunteer App API",
    description="API for Cross Point Baptist Church volunteer signup and management",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
# In production, replace with specific origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(volunteers.router, prefix="/api", tags=["volunteers"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "CPBC Volunteer App API", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
