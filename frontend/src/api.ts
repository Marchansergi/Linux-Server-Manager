import type { CpuStats, CurrentUser, MemoryStats, StorageStats, SystemInfo } from "./types";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Not JSON (e.g. a proxy error page): fall back to the status text.
  }
  return response.statusText || `Request failed with status ${response.status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      credentials: "same-origin",
      ...init,
      headers: { Accept: "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server");
  }
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}

export const api = {
  me: () => request<CurrentUser>("/auth/me"),
  login: (username: string, password: string) =>
    request<CurrentUser>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  systemInfo: () => request<SystemInfo>("/system/info"),
  cpu: () => request<CpuStats>("/system/cpu"),
  memory: () => request<MemoryStats>("/system/memory"),
  storage: () => request<StorageStats>("/system/storage"),
};

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}
