"""Response and request models exposed by the API."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.security import MAX_PASSWORD_LENGTH


class HealthStatus(BaseModel):
    status: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class CurrentUser(BaseModel):
    username: str


class SystemInfo(BaseModel):
    hostname: str
    os_name: str | None
    kernel: str
    architecture: str
    boot_time: datetime
    uptime_seconds: int


class CpuStats(BaseModel):
    usage_percent: float
    per_core_percent: list[float]
    logical_cores: int | None
    physical_cores: int | None
    load_average: tuple[float, float, float] | None
    frequency_mhz: float | None


class SwapStats(BaseModel):
    total_bytes: int
    used_bytes: int
    percent: float


class MemoryStats(BaseModel):
    total_bytes: int
    available_bytes: int
    # Memory that is not available to new applications (total - available).
    used_bytes: int
    percent: float
    swap: SwapStats


class Partition(BaseModel):
    device: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


class StorageStats(BaseModel):
    partitions: list[Partition]
