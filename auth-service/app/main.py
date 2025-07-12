from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.config import get_settings
from app.routers import auth, health
from app.telemetry import instrument_app, check_zipkin_connection


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP Bearer for token authentication
security = HTTPBearer(auto_error=False)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application
    """
    # Startup
    logger.info("======== AUTH SERVICE STARTING UP ========")

    # Log environment variables
    logger.info("Environment variables:")
    for key in ['ZIPKIN_URL', 'OTEL_TRACES_EXPORTER', 'OTEL_EXPORTER_ZIPKIN_ENDPOINT',
                'OTEL_EXPORTER_ZIPKIN_PROTOCOL', 'OTEL_SERVICE_NAME']:
        logger.info(f"{key}: {os.environ.get(key, 'NOT SET')}")

    # Check Zipkin connectivity
    zipkin_status = check_zipkin_connection()
    logger.info(f"Zipkin connectivity: {'OK' if zipkin_status else 'FAILED'}")

    logger.info("Auth service started successfully")

    yield

    # Shutdown
    logger.info("======== AUTH SERVICE SHUTTING DOWN ========")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization service",
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument the app with OpenTelemetry
instrument_app(app)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(health.router, tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Auth Service is running",
        "version": settings.API_VERSION,
        "service": "auth-service"
    }


@app.get("/protected")
async def protected_endpoint(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Example protected endpoint"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Bearer token required")

    # In a real app, you would verify the token here
    return {"message": "This is a protected endpoint", "token": credentials.credentials}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)