"""
HealthPulse Registry Backend API
FastAPI application for managing ETL jobs and health facility data
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import etl_jobs, overpass

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HealthPulse Registry API",
    description="Backend API for health facility registry and ETL pipeline management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)



# CORS middleware - allow frontend to access API
# If CORS_ORIGINS is not explicitly set, allow all HTTP origins for network access (e.g., 192.168.x.x)
# Use regex pattern to match any http:// origin
env_cors_origins = os.getenv("CORS_ORIGINS")
default_origins = "http://localhost:5173,http://localhost:3000,http://localhost:3001,http://127.0.0.1:5173,http://127.0.0.1:3001,http://localhost:8002,http://127.0.0.1:8002"
if not env_cors_origins:
    cors_origins = []  # Empty list when using regex
    cors_regex = r"http://.*"  # Allow any http origin
    allow_creds = False  # Must be False when using wildcard/regex
else:
    cors_origins = env_cors_origins.split(",")
    cors_regex = None
    allow_creds = True

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=cors_regex,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(etl_jobs.router, prefix="/api/v1", tags=["ETL Jobs"])
app.include_router(overpass.router, prefix="/api/v1/overpass", tags=["Overpass API"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "HealthPulse Registry API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

