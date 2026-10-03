import type { AuthResponse, Task, User } from "@/types";

export const getApiBase = (): string => {
  const envBase = process.env.NEXT_PUBLIC_API_BASE;
  if (envBase && !envBase.includes("localhost") && !envBase.includes("127.0.0.1")) {
    return envBase;
  }
  if (
    typeof window !== "undefined" &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1"
  ) {
    return "https://apex-backend-fihp.onrender.com/api/v1";
  }
  return envBase || "http://localhost:8000/api/v1";
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

const handleJsonResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      if (!window.location.pathname.startsWith("/login")) {
        const currentPath = window.location.pathname + window.location.search;
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination
        window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
      }
    }

    let message = `Request failed with status ${response.status}`;
    try {
      const errorBody = await response.json();
      message = errorBody.detail ?? errorBody.message ?? JSON.stringify(errorBody);
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
};

export const api = {
  register: async (data: { email: string; password: string; full_name?: string }): Promise<User> => {
    const response = await fetch(`${getApiBase()}/auth/register`, {
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
    const response = await fetch(`${getApiBase()}/auth/login`, {
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
    const response = await fetch(`${getApiBase()}/auth/me`, {
      headers: authHeaders(true),
    });
    return handleJsonResponse<User>(response);
  },

  checkHealth: async (): Promise<boolean> => {
    try {
      const response = await fetch(`${getBackendUrl()}/health`);
      return response.ok;
    } catch {
      return false;
    }
  },

  createTask: async (goal: string, title?: string): Promise<Task> => {
    const response = await fetch(`${getApiBase()}/tasks/`, {
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
    const response = await fetch(`${getApiBase()}/tasks/`, {
      headers: authHeaders(true),
    });
    return handleJsonResponse<Task[]>(response);
  },

  getTask: async (id: number): Promise<Task> => {
    const response = await fetch(`${getApiBase()}/tasks/${id}`, {
      headers: authHeaders(true),
    });
    return handleJsonResponse<Task>(response);
  },

  deleteTask: async (id: number): Promise<{ detail: string }> => {
    const response = await fetch(`${getApiBase()}/tasks/${id}`, {
      method: "DELETE",
      headers: authHeaders(true),
    });
    return handleJsonResponse<{ detail: string }>(response);
  },

  approveTask: async (id: number): Promise<Task> => {
    const response = await fetch(`${getApiBase()}/tasks/${id}/approve`, {
      method: "POST",
      headers: authHeaders(true),
    });
    return handleJsonResponse<Task>(response);
  },

  rejectTask: async (id: number): Promise<Task> => {
    const response = await fetch(`${getApiBase()}/tasks/${id}/reject`, {
      method: "POST",
      headers: authHeaders(true),
    });
    return handleJsonResponse<Task>(response);
  },

  runTaskBackground: async (id: number): Promise<{ task_id: number; status: string; mode: string }> => {
    const response = await fetch(`${getApiBase()}/tasks/${id}/run-background`, {
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

    fetch(`${getApiBase()}/tasks/${id}/run`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "text/event-stream",
      },
      signal: abortController.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Execution stream failed with status ${response.status}`);
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
          const lines = buffer.split("\n\n");
          buffer = lines.pop() ?? "";

          for (const chunk of lines) {
            const trimmed = chunk.trim();
            if (!trimmed.startsWith("data:")) continue;

            const payload = trimmed.slice(5).trim();
            if (payload === "[DONE]") {
              closed = true;
              onDone();
              return;
            }

            try {
              const parsed = JSON.parse(payload);
              onEvent(parsed);
            } catch (e) {
              console.warn("Could not parse stream payload", payload, e);
            }
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
        await fetch(`${getApiBase()}/auth/logout`, {
          method: "POST",
          headers: authHeaders(true),
        });
      } catch {
        // Silently continue local cleanup if network fails
      }
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.href = "/login";
    }
  },
};
