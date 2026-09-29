"""RAM and swap usage."""

import psutil

from app.schemas import MemoryStats, SwapStats


def get_memory_stats() -> MemoryStats:
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return MemoryStats(
        total_bytes=memory.total,
        available_bytes=memory.available,
        used_bytes=memory.total - memory.available,
        percent=memory.percent,
        swap=SwapStats(total_bytes=swap.total, used_bytes=swap.used, percent=swap.percent),
    )
