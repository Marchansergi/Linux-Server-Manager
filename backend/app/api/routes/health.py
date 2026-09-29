from fastapi import APIRouter

from app.schemas import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> HealthStatus:
    return HealthStatus(status="ok")
