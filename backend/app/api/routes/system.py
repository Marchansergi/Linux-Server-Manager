"""Read-only system metrics. Every endpoint requires an authenticated session."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SettingsDep, get_current_user
from app.schemas import CpuStats, MemoryStats, StorageStats, SystemInfo
from app.services.cpu import get_cpu_stats
from app.services.memory import get_memory_stats
from app.services.storage import StorageUnavailableError, get_storage_stats
from app.services.system_info import get_system_info

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"], dependencies=[Depends(get_current_user)])


@router.get("/info")
def system_info(settings: SettingsDep) -> SystemInfo:
    return get_system_info(settings.host_root)


@router.get("/cpu")
def cpu() -> CpuStats:
    return get_cpu_stats()


@router.get("/memory")
def memory() -> MemoryStats:
    return get_memory_stats()


@router.get("/storage")
def storage(settings: SettingsDep) -> StorageStats:
    try:
        return get_storage_stats(settings.host_root)
    except StorageUnavailableError as exc:
        logger.error("Storage stats failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Storage data unavailable"
        ) from exc
