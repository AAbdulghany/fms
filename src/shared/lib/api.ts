const API_BASE = "/api/v1";

export function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}

export function getRefreshToken(): string | null {
  return localStorage.getItem("refresh_token");
}

async function request(
  path: string,
  options: RequestInit & { json?: unknown } = {},
  tokenOverride?: string | null
): Promise<Response> {
  const headers: HeadersInit = {
    ...(options.headers || {}),
  };
  const token = tokenOverride ?? getAccessToken();
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  let body = options.body;
  if (options.json !== undefined) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  }
  return fetch(`${API_BASE}${path}`, { ...options, headers, body });
}

async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  const res = await request("/auth/refresh", {
    method: "POST",
    json: { refresh_token: refreshToken },
  }, null);

  if (!res.ok) {
    clearTokens();
    return null;
  }

  const data = (await res.json()) as { access_token: string; refresh_token: string };
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

function redirectToLogin() {
  clearTokens();
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { json?: unknown } = {}
): Promise<T> {
  let res = await request(path, options);

  if (res.status === 401 && !path.startsWith("/auth/")) {
    const nextAccessToken = await tryRefreshToken();
    if (nextAccessToken) {
      res = await request(path, options, nextAccessToken);
    } else {
      redirectToLogin();
      throw new Error(JSON.stringify({ detail: "INVALID_TOKEN" }));
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401) {
      redirectToLogin();
    }
    throw new Error(JSON.stringify(err));
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type");
  if (ct?.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res.text() as Promise<T>;
}

export { resolveApiError, parseApiError } from "./errors";

/** Authenticated binary download (e.g. generated report PDF). */
export async function apiFetchBlob(path: string): Promise<Blob> {
  let res = await request(path, { method: "GET" });

  if (res.status === 401 && !path.startsWith("/auth/")) {
    const nextAccessToken = await tryRefreshToken();
    if (nextAccessToken) {
      res = await request(path, { method: "GET" }, nextAccessToken);
    } else {
      redirectToLogin();
      throw new Error(JSON.stringify({ detail: "INVALID_TOKEN" }));
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401) {
      redirectToLogin();
    }
    throw new Error(JSON.stringify(err));
  }
  return res.blob();
}

/** Open a PDF (or other blob) from an authenticated GET in a new tab. */
export async function openAuthenticatedBlob(path: string): Promise<void> {
  const blob = await apiFetchBlob(path);
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  window.setTimeout(() => URL.revokeObjectURL(url), 120_000);
}

/** Download a file from an authenticated GET. */
export async function downloadAuthenticatedFile(path: string, filename: string): Promise<void> {
  const blob = await apiFetchBlob(path);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function notifyAuthTokenChanged() {
  window.dispatchEvent(new Event("fms-auth-token-changed"));
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
  notifyAuthTokenChanged();
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  notifyAuthTokenChanged();
}
