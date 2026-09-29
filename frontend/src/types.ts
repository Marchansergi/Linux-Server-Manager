// Mirrors backend/app/schemas.py.

export interface CurrentUser {
  username: string;
}

export interface SystemInfo {
  hostname: string;
  os_name: string | null;
  kernel: string;
  architecture: string;
  boot_time: string;
  uptime_seconds: number;
}

export interface CpuStats {
  usage_percent: number;
  per_core_percent: number[];
  logical_cores: number | null;
  physical_cores: number | null;
  load_average: [number, number, number] | null;
  frequency_mhz: number | null;
}

export interface MemoryStats {
  total_bytes: number;
  available_bytes: number;
  used_bytes: number;
  percent: number;
  swap: { total_bytes: number; used_bytes: number; percent: number };
}

export interface Partition {
  device: string;
  mountpoint: string;
  fstype: string;
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  percent: number;
}

export interface StorageStats {
  partitions: Partition[];
}
