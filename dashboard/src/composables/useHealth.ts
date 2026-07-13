import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'

/** Health-Zustand: ok = grün, degraded = orange (prüft/unklar), down = rot. */
export type HealthStatus = 'ok' | 'degraded' | 'down'

interface HealthResponse {
  status: string
  version: string
}

/** Pollt den /health-Endpoint und liefert Ampel-Status + Version. */
export function useHealth(intervalMs = 15000): {
  status: Ref<HealthStatus>
  version: Ref<string | null>
  start: () => void
  stop: () => void
} {
  const status = ref<HealthStatus>('degraded') // initial: wird geprüft
  const version = ref<string | null>(null)
  let timer: ReturnType<typeof setInterval> | undefined

  async function check(): Promise<void> {
    try {
      const health = await apiClient.get<HealthResponse>('/health')
      version.value = health.version
      status.value = health.status === 'ok' ? 'ok' : 'degraded'
    } catch (err) {
      status.value = 'down'
      consola.error('useHealth.check', err)
    }
  }

  function start(): void {
    void check()
    timer = setInterval(() => void check(), intervalMs)
  }

  function stop(): void {
    if (timer) clearInterval(timer)
  }

  return { status, version, start, stop }
}
