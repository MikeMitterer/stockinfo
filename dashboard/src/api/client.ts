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

/**
 * Statuscodes, die trotz `!response.ok` eine **Antwort** sind, kein Fehler.
 *
 * Nur die Diagnosewege `/ready` und `/operational` brauchen das: Sie tragen
 * ihre Aussage im Körper und benutzen den Statuscode als zweites Merkmal —
 * „nicht bedienbar" ist dort ein Zustand, kein Ausfall. Ohne diese Liste käme
 * davon ein `ApiError` mit dem JSON als Text an, und der Aufrufer müsste ihn
 * wieder auseinandernehmen.
 *
 * Alles andere bleibt ein Fehler: Ein `404` auf `/ready` heißt, dass etwas
 * ganz anderes antwortet als der eigene Server.
 */
const PROBE_STATUS: readonly number[] = [503]

/**
 * Der **eine** Transportweg zur API.
 *
 * @param path - Pfad hinter `API_BASE_URL`.
 * @param init - Methode und Körper.
 * @param alsoOk - Statuscodes, die trotz `!ok` als Antwort gelten.
 * @returns Der decodierte Körper; `undefined` bei `204`.
 */
async function request<T>(
  path: string,
  init?: RequestInit,
  alsoOk: readonly number[] = [],
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok && !alsoOk.includes(response.status)) {
    const detail = await response.text().catch(() => '')
    throw new ApiError(response.status, detail)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export const apiClient = {
  get: <T>(path: string): Promise<T> => request<T>(path),
  /** Für die Diagnosewege: `503` ist dort eine Antwort, siehe `PROBE_STATUS`. */
  probe: <T>(path: string): Promise<T> => request<T>(path, undefined, PROBE_STATUS),
  post: <T>(path: string, body?: unknown): Promise<T> =>
    request<T>(path, { method: 'POST', ...(body === undefined ? {} : { body: JSON.stringify(body) }) }),
  put: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  del: (path: string): Promise<void> => request<void>(path, { method: 'DELETE' }),
}
