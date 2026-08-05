import type { Adhesion } from '@/types';

/**
 * Regroupement des adhésions en « familles ».
 *
 * Une famille, c'est simplement l'ensemble des adhésions portant la même adresse
 * email de contact. Le regroupement se fait **côté client**, à partir des codes
 * mémorisés dans `localStorage` : il n'existe volontairement aucune route publique
 * qui liste les adhésions d'un email, ce serait une énumération offerte à qui
 * devine une adresse. Ce navigateur ne peut donc regrouper que ce qu'il a lui-même
 * créé, ce qui est exactement le cas d'usage visé (« j'inscris ma famille »).
 *
 * Même parti pris que `pricing.ts` et `documents.ts` : des fonctions pures,
 * testables, plutôt que la logique éparpillée dans les composants.
 */

const RECENT_CODES_KEY = 'recentCodes';

/**
 * Une famille nombreuse tient dans la liste : à 5 (l'ancienne limite), le
 * quatrième enfant chassait le parent servant de référence.
 */
export const MAX_RECENT_CODES = 20;

/** Coordonnées communes à toute la famille, recopiées sur chaque nouveau membre. */
export interface FamilyContact {
  email: string;
  telephone: string;
  nom_rue: string;
  code_postal: string;
  ville: string;
}

export interface Family {
  /** Email de contact, normalisé (minuscules, sans espaces). */
  email: string;
  /** Membres, du plus ancien au plus récent. */
  members: Adhesion[];
  /** Premier membre créé : c'est lui qui fournit les coordonnées de la famille. */
  reference: Adhesion;
}

export const readRecentCodes = (): string[] => {
  const raw = localStorage.getItem(RECENT_CODES_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    // Dédoublonnage : l'implémentation précédente empilait sans vérifier, un
    // navigateur déjà utilisé peut donc porter deux fois le même code — qui
    // apparaîtrait deux fois dans sa famille.
    return [...new Set(parsed.filter((c): c is string => typeof c === 'string'))];
  } catch {
    // Entrée corrompue : mieux vaut repartir de zéro que planter le chargement.
    return [];
  }
};

/** Ajoute un code en tête de la liste, sans doublon, et tronque à `MAX_RECENT_CODES`. */
export const rememberCode = (code: string): void => {
  const codes = readRecentCodes().filter(c => c !== code);
  codes.unshift(code);
  localStorage.setItem(RECENT_CODES_KEY, JSON.stringify(codes.slice(0, MAX_RECENT_CODES)));
};

/** Clé de regroupement : l'email tel que saisi peut varier en casse d'un membre à l'autre. */
export const familyKey = (email: string): string => email.trim().toLowerCase();

/**
 * Membre de référence d'une famille : le premier créé, c'est-à-dire le plus petit
 * `id`. Le code d'accès est aléatoire et n'ordonne rien, et l'ordre de
 * `localStorage` ne survit ni à un autre navigateur ni à une saisie manuelle —
 * `id` est le seul témoin fiable de l'ordre de création.
 */
export const referenceMember = (members: Adhesion[]): Adhesion =>
  members.reduce((first, m) => ((m.id ?? 0) < (first.id ?? 0) ? m : first));

/**
 * Regroupe des adhésions par email. Les familles sortent dans l'ordre de première
 * apparition (donc, si on part de `readRecentCodes()`, la plus récemment servie
 * en tête), les membres triés par ordre de création.
 */
export const groupByFamily = (adhesions: Adhesion[]): Family[] => {
  const groups = new Map<string, Adhesion[]>();
  for (const adhesion of adhesions) {
    const key = familyKey(adhesion.email);
    const members = groups.get(key);
    if (members) {
      members.push(adhesion);
    } else {
      groups.set(key, [adhesion]);
    }
  }

  return [...groups.entries()].map(([email, members]) => {
    const sorted = [...members].sort((a, b) => (a.id ?? 0) - (b.id ?? 0));
    return { email, members: sorted, reference: referenceMember(sorted) };
  });
};

/** Extrait d'une adhésion les seuls champs partagés par toute la famille. */
export const familyContact = (adhesion: Adhesion): FamilyContact => ({
  email: adhesion.email,
  telephone: adhesion.telephone ?? '',
  nom_rue: adhesion.nom_rue ?? '',
  code_postal: adhesion.code_postal ?? '',
  ville: adhesion.ville ?? '',
});
