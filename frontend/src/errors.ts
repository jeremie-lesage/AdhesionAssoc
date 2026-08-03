import axios from 'axios';

/**
 * Lecture des erreurs axios sans `any`.
 *
 * Un `catch` livre un `unknown` : l'erreur peut venir de l'API (réponse HTTP),
 * du réseau (pas de `response`) ou d'un bug du code appelant. Ces deux helpers
 * sont le seul endroit qui fait le tri — même parti pris que `pricing.ts` et
 * `documents.ts`, où la règle vit à un seul endroit.
 */

/** Vrai si l'API a répondu 401 : le jeton est absent, expiré ou révoqué. */
export function isUnauthorized(err: unknown): boolean {
  return axios.isAxiosError(err) && err.response?.status === 401;
}

/**
 * Message affichable. Le `detail` renvoyé par l'API est plus parlant que le
 * message axios générique, mais FastAPI y met une liste sur les erreurs de
 * validation (422) : on ne le retient que s'il s'agit d'une chaîne, sinon on
 * retombe sur le message de l'exception.
 */
export function errorDetail(err: unknown, fallback = 'Une erreur est survenue.'): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    return typeof detail === 'string' ? detail : err.message;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return fallback;
}
