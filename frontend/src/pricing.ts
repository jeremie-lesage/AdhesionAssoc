/**
 * Règles de tarification, partagées par le formulaire public et le back-office.
 *
 * Cette logique était dupliquée dans Etape3_Activites, Etape4_Resume,
 * AdhesionAdminView et AdhesionDetailView — avec des variantes (`|| 0` ici,
 * pas là). Elle est ici pure et testée : voir pricing.spec.ts.
 */
import type { Activity } from '@/types';

/** Commune dont les habitants bénéficient du tarif résident. */
export const RESIDENT_CITY = 'fauverney';

/**
 * Un adhérent est résident si sa ville est celle du foyer rural.
 *
 * La comparaison est insensible à la casse uniquement — voir pricing.spec.ts
 * pour les cas limites (espaces, accents) laissés en suspens.
 */
export function isResident(ville: string | null | undefined): boolean {
  return !!ville && ville.toLowerCase() === RESIDENT_CITY;
}

/**
 * Tarif d'une activité pour un adhérent donné.
 *
 * Renvoie `undefined` si l'activité n'a pas de tarif renseigné pour ce profil :
 * l'affichage doit pouvoir distinguer « gratuit » de « non renseigné ».
 */
export function activityPrice(
  activity: Pick<Activity, 'resident_price' | 'external_price'>,
  ville: string | null | undefined,
): number | undefined {
  return isResident(ville) ? activity.resident_price : activity.external_price;
}

/** Somme des tarifs des activités, les tarifs manquants comptant pour 0. */
export function activitiesCost(
  activities: Pick<Activity, 'resident_price' | 'external_price'>[],
  ville: string | null | undefined,
): number {
  return activities.reduce((total, activity) => total + (activityPrice(activity, ville) ?? 0), 0);
}

/**
 * Montant total dû : adhésion + activités - réduction, jamais négatif.
 *
 * Une réduction supérieure au dû ne produit pas de remboursement.
 */
export function adhesionTotal(adhesion: {
  ville: string | null | undefined;
  activities: Pick<Activity, 'resident_price' | 'external_price'>[];
  adhesion_amount?: number | null;
  discount_amount?: number | null;
}): number {
  const subtotal = (adhesion.adhesion_amount || 0) + activitiesCost(adhesion.activities, adhesion.ville);
  return Math.max(subtotal - (adhesion.discount_amount || 0), 0);
}
