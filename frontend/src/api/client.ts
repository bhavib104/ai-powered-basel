/**
 * Minimal typed HTTP client for the backend API.
 *
 * Only real endpoints are called.  When the backend is unavailable the
 * helpers throw a descriptive ``ApiError`` so the UI can show an honest
 * error state rather than fake data.
 */

// The backend (uvicorn) listens on IPv4 127.0.0.1 by default, so we default to
// that exact address to avoid IPv6/IPv4 localhost ambiguity in browsers.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  public readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      headers: { Accept: "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(
      `Could not reach the backend at ${API_BASE_URL}. Is it running?`,
    );
  }

  if (!response.ok) {
    throw new ApiError(`Request failed with status ${response.status}`, response.status);
  }

  return (await response.json()) as T;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  checks: Record<string, string>;
}

export const api = {
  baseUrl: API_BASE_URL,
  health: () => request<HealthResponse>("/api/v1/health"),
};
