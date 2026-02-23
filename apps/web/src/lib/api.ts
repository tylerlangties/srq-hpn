const SERVER_API_BASE_URL =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const CLIENT_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

type ApiRequestOptions = {
  cache?: RequestCache;
  revalidate?: number;
  tags?: string[];
};

function stripTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function toApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  if (typeof window === "undefined") {
    return `${stripTrailingSlash(SERVER_API_BASE_URL)}${path}`;
  }

  if (!CLIENT_API_BASE_URL) {
    return path;
  }

  return `${stripTrailingSlash(CLIENT_API_BASE_URL)}${path}`;
}

export async function apiGet<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const fetchOptions: RequestInit & { next?: { revalidate?: number; tags?: string[] } } = {
    cache:
      options.cache ??
      (options.revalidate !== undefined || options.tags !== undefined ? "force-cache" : "no-store"),
    credentials: "include",
  };

  if (options.revalidate !== undefined || options.tags !== undefined) {
    fetchOptions.next = {
      revalidate: options.revalidate,
      tags: options.tags,
    };
  }

  const res = await fetch(toApiUrl(path), fetchOptions);

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }

  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(toApiUrl(path), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
    credentials: "include",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }

  return res.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(toApiUrl(path), {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
    credentials: "include",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }

  return res.json() as Promise<T>;
}
