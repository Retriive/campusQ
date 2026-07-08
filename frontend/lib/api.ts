const DEFAULT_API_BASE_URL = "http://localhost:8000"

/**
 * Canonical CampusQ backend base URL for browser and server components.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.trim() || DEFAULT_API_BASE_URL

export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  return fetch(`${API_BASE_URL}${normalizedPath}`, init)
}
