import { beforeEach } from 'vitest'

/**
 * Node 25 définit lui-même un global `localStorage` qui, sans l'option
 * `--localstorage-file`, se réduit à un objet vide — sans `setItem` ni
 * `getItem`. Il masque celui de jsdom, si bien que tout code testé touchant au
 * Web Storage échoue avec « localStorage.setItem is not a function », alors que
 * le même code marche dans un vrai navigateur.
 *
 * On installe donc une implémentation mémoire. Elle est remise à zéro avant
 * chaque test : `localStorage` est un état global, sans quoi l'ordre des tests
 * changerait leurs résultats (même raison que `reset_rate_limiter` côté backend).
 */
class MemoryStorage implements Storage {
  private entries = new Map<string, string>()

  get length(): number {
    return this.entries.size
  }

  key(index: number): string | null {
    return [...this.entries.keys()][index] ?? null
  }

  getItem(key: string): string | null {
    return this.entries.get(key) ?? null
  }

  setItem(key: string, value: string): void {
    this.entries.set(String(key), String(value))
  }

  removeItem(key: string): void {
    this.entries.delete(key)
  }

  clear(): void {
    this.entries.clear()
  }
}

const storage = new MemoryStorage()

for (const target of [globalThis, window]) {
  Object.defineProperty(target, 'localStorage', {
    value: storage,
    configurable: true,
    writable: true,
  })
}

beforeEach(() => {
  storage.clear()
})
