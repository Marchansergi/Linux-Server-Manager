import { useCallback, useEffect, useRef, useState } from "react";
import { api, isUnauthorized } from "./api";
import type { CpuStats, MemoryStats, StorageStats, SystemInfo } from "./types";

export const POLL_INTERVAL_MS = 5_000;

export interface Resource<T> {
  data: T | null;
  error: string | null;
}

export interface DashboardData {
  info: Resource<SystemInfo>;
  cpu: Resource<CpuStats>;
  memory: Resource<MemoryStats>;
  storage: Resource<StorageStats>;
}

const EMPTY: Resource<never> = { data: null, error: null };

function settle<T>(previous: Resource<T>, result: PromiseSettledResult<T>): Resource<T> {
  if (result.status === "fulfilled") return { data: result.value, error: null };
  const reason: unknown = result.reason;
  // Keep the last good value so a transient error does not blank the card.
  return { data: previous.data, error: reason instanceof Error ? reason.message : String(reason) };
}

/** Polls the metrics endpoints while the page is visible. */
export function useDashboardData(onUnauthorized: () => void): DashboardData {
  const [data, setData] = useState<DashboardData>({
    info: EMPTY,
    cpu: EMPTY,
    memory: EMPTY,
    storage: EMPTY,
  });
  const onUnauthorizedRef = useRef(onUnauthorized);
  onUnauthorizedRef.current = onUnauthorized;

  const refresh = useCallback(async (isActive: () => boolean) => {
    const [info, cpu, memory, storage] = await Promise.allSettled([
      api.systemInfo(),
      api.cpu(),
      api.memory(),
      api.storage(),
    ]);
    if (!isActive()) return;
    if ([info, cpu, memory, storage].some((r) => r.status === "rejected" && isUnauthorized(r.reason))) {
      onUnauthorizedRef.current();
      return;
    }
    setData((prev) => ({
      info: settle(prev.info, info),
      cpu: settle(prev.cpu, cpu),
      memory: settle(prev.memory, memory),
      storage: settle(prev.storage, storage),
    }));
  }, []);

  useEffect(() => {
    let active = true;
    let timer: number | undefined;
    const isActive = () => active;

    const tick = async () => {
      if (document.visibilityState === "visible") await refresh(isActive);
      if (active) timer = window.setTimeout(tick, POLL_INTERVAL_MS);
    };
    const onVisibilityChange = () => {
      if (document.visibilityState !== "visible" || !active) return;
      window.clearTimeout(timer);
      void tick();
    };

    void tick();
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      active = false;
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [refresh]);

  return data;
}
