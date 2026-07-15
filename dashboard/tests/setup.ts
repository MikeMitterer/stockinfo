// Node ≥22 definiert ein eigenes localStorage-Global (Web Storage API), das ohne
// --localstorage-file undefined bleibt — dadurch übernimmt Vitest die
// jsdom-Implementierung nicht. Für Tests wird hier ein In-Memory-Ersatz gesetzt.

/** Minimaler In-Memory-Ersatz für die Storage-API (localStorage in Tests). */
class MemoryStorage implements Storage {
  private store = new Map<string, string>()

  get length(): number {
    return this.store.size
  }

  clear(): void {
    this.store.clear()
  }

  getItem(key: string): string | null {
    return this.store.get(key) ?? null
  }

  key(index: number): string | null {
    return [...this.store.keys()][index] ?? null
  }

  removeItem(key: string): void {
    this.store.delete(key)
  }

  setItem(key: string, value: string): void {
    this.store.set(key, String(value))
  }
}

if (typeof globalThis.localStorage === 'undefined') {
  Object.defineProperty(globalThis, 'localStorage', {
    value: new MemoryStorage(),
    configurable: true,
    writable: true,
  })
}
