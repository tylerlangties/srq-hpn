import { apiGet, apiPost } from "@/lib/api";
import { API_PATHS } from "@/lib/api-paths";
import type { AuthUser, LoginRequest } from "@/types/auth";

export async function login(body: LoginRequest): Promise<AuthUser> {
  return apiPost<AuthUser>(API_PATHS.auth.login, body);
}

export async function logout(): Promise<{ ok: boolean }> {
  return apiPost<{ ok: boolean }>(API_PATHS.auth.logout, {});
}

export async function getCurrentUser(): Promise<AuthUser> {
  return apiGet<AuthUser>(API_PATHS.auth.me);
}

export function extractApiStatus(error: unknown): number | null {
  if (!(error instanceof Error)) {
    return null;
  }
  const match = error.message.match(/^API\s+(\d{3})\b/);
  if (!match) {
    return null;
  }
  return Number.parseInt(match[1], 10);
}
