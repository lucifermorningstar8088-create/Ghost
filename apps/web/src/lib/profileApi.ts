/** Typed client for the authenticated, tenant-scoped Ghost profile API.
 *
 * Callers obtain access tokens from a trusted authentication flow and pass
 * them to requests. This module never persists tokens or accepts tenant IDs.
 */
export type GhostPlatform = "youtube" | "facebook" | "instagram";

export interface GhostProfile {
  profile_id: string;
  connected_account_id: string;
  platform: GhostPlatform;
  display_name: string;
  profile_version: number;
  profile_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface GhostProfileInput {
  profile_id: string;
  connected_account_id: string;
  platform: GhostPlatform;
  display_name: string;
  profile_version?: number;
  profile_data?: Record<string, unknown>;
}

export interface GhostProfilePatch {
  connected_account_id?: string;
  platform?: GhostPlatform;
  display_name?: string;
  profile_version?: number;
  profile_data?: Record<string, unknown>;
}

export class GhostApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "GhostApiError";
  }
}

const configuredBaseUrl = (import.meta.env.VITE_GHOST_API_URL as string | undefined)
  ?? (import.meta.env.VITE_API_BASE_URL as string | undefined)
  ?? "http://localhost:8000";

export function getGhostApiBaseUrl(): string {
  return configuredBaseUrl.replace(/\/$/, "");
}

async function request<T>(path: string, accessToken: string, init: RequestInit = {}): Promise<T> {
  if (!accessToken.trim()) {
    throw new GhostApiError("Sign in before accessing saved profiles.", 401);
  }

  let response: Response;
  try {
    response = await fetch(`${getGhostApiBaseUrl()}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${accessToken}`,
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new GhostApiError("Ghost API is unreachable. Check the API URL and service status.", 0);
  }

  if (!response.ok) {
    const messages: Record<number, string> = {
      401: "Your session is missing or expired. Sign in again.",
      403: "Your account is not assigned to a Ghost workspace.",
      404: "This profile is not available in your workspace.",
      409: "A profile with this ID already exists.",
      422: "Some profile fields are invalid.",
      503: "Profile storage or authentication is temporarily unavailable.",
    };
    throw new GhostApiError(messages[response.status] ?? `Ghost API request failed (${response.status}).`, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function listGhostProfiles(accessToken: string): Promise<GhostProfile[]> {
  return request<GhostProfile[]>("/api/v1/profiles", accessToken);
}

export function getGhostProfile(accessToken: string, profileId: string): Promise<GhostProfile> {
  return request<GhostProfile>(`/api/v1/profiles/${encodeURIComponent(profileId)}`, accessToken);
}

export function createGhostProfile(accessToken: string, input: GhostProfileInput): Promise<GhostProfile> {
  return request<GhostProfile>("/api/v1/profiles", accessToken, { method: "POST", body: JSON.stringify(input) });
}

export function updateGhostProfile(accessToken: string, profileId: string, patch: GhostProfilePatch): Promise<GhostProfile> {
  return request<GhostProfile>(`/api/v1/profiles/${encodeURIComponent(profileId)}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteGhostProfile(accessToken: string, profileId: string): Promise<void> {
  return request<void>(`/api/v1/profiles/${encodeURIComponent(profileId)}`, accessToken, { method: "DELETE" });
}
