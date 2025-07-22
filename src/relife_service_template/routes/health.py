import time

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint that returns service status and current timestamp."""

    return {"status": "healthy", "timestamp": int(time.time())}
