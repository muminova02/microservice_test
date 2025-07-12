from fastapi import APIRouter

from app.models import HealthResponse
from app.telemetry import get_tracer, logger

# Setup
tracer = get_tracer()
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring
    """
    with tracer.start_as_current_span("health_check"):
        logger.info("Health check requested")

        return {
            "status": "healthy", 
            "service": "auth-service"
        }
