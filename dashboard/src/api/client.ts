import { API_BASE_URL } from '../config'

/** Fehler mit HTTP-Status und Detailtext aus der API. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(`API ${status}: ${detail}`)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText)
    throw new ApiError(response.status, detail)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

/**
 * Wie `request`, aber ein `503` ist hier eine **Antwort**, kein Fehler.
 *
 * Die Diagnosewege `/ready` und `/operational` tragen ihre Aussage im Körper
 * und benutzen den Statuscode als zweites Merkmal — „nicht bedienbar" ist dort
 * ein Zustand, kein Ausfall. Über `request` käme davon nur ein `ApiError` mit
 * dem JSON als Text an, und der Aufrufer müsste ihn wieder auseinandernehmen.
 *
 * Alles außer `200` und `503` bleibt ein Fehler: Ein `404` auf `/ready` heißt,
 * dass etwas ganz anderes antwortet als der eigene Server.
 */
async function probeRequest<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok && response.status !== 503) {
    const detail = await response.text().catch(() => response.statusText)
    throw new ApiError(response.status, detail)
  }
  return (await response.json()) as T
}

export const apiClient = {
  get: <T>(path: string): Promise<T> => request<T>(path),
  probe: <T>(path: string): Promise<T> => probeRequest<T>(path),
  post: <T>(path: string): Promise<T> => request<T>(path, { method: 'POST' }),
  put: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  del: (path: string): Promise<void> => request<void>(path, { method: 'DELETE' }),
}
