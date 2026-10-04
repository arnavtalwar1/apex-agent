import type { AuthResponse, Task, User } from "@/types";

export const getApiBase = (): string => {
  const envBase = process.env.NEXT_PUBLIC_API_BASE;
  if (envBase && !envBase.includes("localhost") && !envBase.includes("127.0.0.1")) {
    return envBase.replace(/\/+$/, "");
  }
  if (
    typeof window !== "undefined" &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1"
  ) {
    return "https://apex-backend-fihp.onrender.com/api/v1";
  }
  return (envBase || "http://localhost:8000/api/v1").replace(/\/+$/, "");
};

export const getBackendUrl = (): string => {
  return getApiBase().replace(/\/api\/v1\/?$/, "");
};

export const getToken = (): string | null => {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem("access_token");
};

export const authHeaders = (withAuth = true): Record<string, string> => {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (withAuth) {
    const token = getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  return headers;
};

export const clearSession = () => {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

const errorMessage = async (response: Response): Promise<string> => {
  try {
    const body = await response.json();
    const detail = body.detail ?? body.message;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg ?? "Invalid input").join(". ");
  } catch { /* Responses may be empty or plain text. */ }
  return `Request failed (${response.status}). Please try again.`;
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

const handleJsonResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status);
  return response.json() as Promise<T>;
};

let refreshPromise: Promise<AuthResponse> | null = null;

/** Share token rotation across concurrent requests, then retry each request once. */
const apiFetch = async (url: string, init: RequestInit = {}): Promise<Response> => {
  const headers = new Headers(init.headers);
  const authenticated = headers.has("Authorization");
  const fetchOnce = () => fetch(url, {
    ...init, headers,
    signal: init.signal ?? AbortSignal.timeout(60_000),
  });
  let response = await fetchOnce();
  if (response.status !== 401 || !authenticated || url.includes("/auth/logout")) return response;
  if (typeof window !== "undefined" && localStorage.getItem("refresh_token")) {
    try {
      refreshPromise ??= api.refreshToken().finally(() => { refreshPromise = null; });
      const tokens = await refreshPromise;
      headers.set("Authorization", `Bearer ${tokens.access_token}`);
      response = await fetchOnce();
      if (response.status !== 401) return response;
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) throw error;
    }
  }
  clearSession();
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    const path = window.location.pathname + window.location.search;
    // API utilities run outside React; a full navigation clears stale protected state.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign(`/login?redirect=${encodeURIComponent(path)}`);
  }
  return response;
};

export const api = {
  register: async (data: { email: string; password: string; full_name?: string }): Promise<User> => {
    const response = await apiFetch(`${getApiBase()}/auth/register`, {
      method: "POST",
      headers: authHeaders(false),
      body: JSON.stringify({
        email: data.email,
        password: data.password,
        full_name: data.full_name || "User",
      }),
    });
    return handleJsonResponse<User>(response);
  },

  login: async (data: { email: string; password: string }): Promise<AuthResponse> => {
    const response = await apiFetch(`${getApiBase()}/auth/login`, {
      method: "POST",
      headers: authHeaders(false),
      body: JSON.stringify(data),
    });

    const result = await handleJsonResponse<AuthResponse>(response);
    if (result.access_token && typeof window !== "undefined") {
      localStorage.setItem("access_token", result.access_token);
      if (result.refresh_token) {
        localStorage.setItem("refresh_token", result.refresh_token);
      }
    }
    return result;
  },

  getMe: async (): Promise<User> => {
    const response = await apiFetch(`${getApiBase()}/auth/me`, {
      headers: authHeaders(true),
    });
    return handleJsonResponse<User>(response);
  },

  checkHealth: async (): Promise<boolean> => {
    try {
      const response = await apiFetch(`${getBackendUrl()}/health`);
      return response.ok;
    } catch {
      return false;
    }
  },

  createTask: async (goal: string, title?: string): Promise<Task> => {
    const response = await apiFetch(`${getApiBase()}/tasks/`, {
      method: "POST",
      headers: authHeaders(true),
      body: JSON.stringify({
        goal,
        title: title || (goal.length > 50 ? goal.slice(0, 47) + "..." : goal),
      }),
    });
    return handleJsonResponse<Task>(response);
  },

  listTasks: async (): Promise<Task[]> => {
    const response = await apiFetch(`${getApiBase()}/tasks/`, {
      headers: authHeaders(true),
    });
    return handleJsonResponse<Task[]>(response);
  },

  getTask: async (id: number): Promise<Task> => {
    const response = await apiFetch(`${getApiBase()}/tasks/${id}`, {
      headers: authHeaders(true),
    });
    return handleJsonResponse<Task>(response);
  },

  deleteTask: async (id: number): Promise<{ detail: string }> => {
    const response = await apiFetch(`${getApiBase()}/tasks/${id}`, {
      method: "DELETE",
      headers: authHeaders(true),
    });
    return handleJsonResponse<{ detail: string }>(response);
  },

  approveTask: async (id: number): Promise<Task> => {
    const response = await apiFetch(`${getApiBase()}/tasks/${id}/approve`, {
      method: "POST",
      headers: authHeaders(true),
    });
    return handleJsonResponse<Task>(response);
  },

  rejectTask: async (id: number): Promise<Task> => {
    const response = await apiFetch(`${getApiBase()}/tasks/${id}/reject`, {
      method: "POST",
      headers: authHeaders(true),
    });
    return handleJsonResponse<Task>(response);
  },

  runTaskBackground: async (id: number): Promise<{ task_id: number; status: string; mode: string }> => {
    const response = await apiFetch(`${getApiBase()}/tasks/${id}/run-background`, {
      method: "POST",
      headers: authHeaders(true),
    });
    return handleJsonResponse<{ task_id: number; status: string; mode: string }>(response);
  },

  /**
   * Runs a task using Server-Sent Events (SSE) via streaming fetch.
   * Sends Authorization header natively without token leakage in URL query params.
   */
  runTask: (
    id: number,
    onEvent: (event: Record<string, unknown>) => void,
    onDone: () => void,
    onError?: (error: Error) => void
  ): (() => void) => {
    const token = getToken();
    if (!token) {
      const err = new Error("Not authenticated. Please log in first.");
      if (onError) onError(err);
      return () => {};
    }

    let closed = false;
    const abortController = new AbortController();

    apiFetch(`${getApiBase()}/tasks/${id}/run`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "text/event-stream",
      },
      signal: abortController.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(await errorMessage(response));
        }
        if (!response.body) {
          throw new Error("No response body available from task run");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!closed) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split(/\r?\n\r?\n/);
          buffer = lines.pop() ?? "";

          for (const chunk of lines) {
            const payload = chunk.split(/\r?\n/).filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trimStart()).join("\n").trim();
            if (!payload) continue;
            if (payload === "[DONE]") {
              closed = true;
              onDone();
              return;
            }

            const parsed = JSON.parse(payload);
            onEvent(parsed);
          }
        }

        if (!closed) {
          onDone();
        }
      })
      .catch((err) => {
        if (closed || err.name === "AbortError") return;
        if (onError) onError(err instanceof Error ? err : new Error(String(err)));
      });

    return () => {
      closed = true;
      abortController.abort();
    };
  },

  refreshToken: async (): Promise<AuthResponse> => {
    const refresh_token = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
    if (!refresh_token) {
      throw new Error("No refresh token available");
    }
    const response = await fetch(`${getApiBase()}/auth/refresh`, {
      method: "POST",
      headers: authHeaders(false),
      body: JSON.stringify({ refresh_token }),
      signal: AbortSignal.timeout(60_000),
    });
    const result = await handleJsonResponse<AuthResponse>(response);
    if (result.access_token && typeof window !== "undefined") {
      localStorage.setItem("access_token", result.access_token);
      if (result.refresh_token) {
        localStorage.setItem("refresh_token", result.refresh_token);
      }
    }
    return result;
  },

  logout: async () => {
    if (typeof window !== "undefined") {
      try {
        await apiFetch(`${getApiBase()}/auth/logout`, {
          method: "POST",
          headers: authHeaders(true),
          body: localStorage.getItem("refresh_token") ? JSON.stringify({ refresh_token: localStorage.getItem("refresh_token") }) : undefined,
        });
      } catch {
        // Silently continue local cleanup if network fails
      }
      clearSession();
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.href = "/login";
    }
  },
};
