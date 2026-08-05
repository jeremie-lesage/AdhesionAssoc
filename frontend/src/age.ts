/**
 * Règles d'âge et de catégorie d'adhésion, isolées comme `pricing.ts` et
 * `documents.ts` : le formulaire et le back-office doivent classer un adhérent
 * de la même façon, et cette logique se teste sans monter de composant.
 *
 * Attention : la catégorie est **informative**. Elle ne conditionne pas
 * l'inscription — le caractère enfant/adulte d'une *activité* vient des
 * booléens `is_child_activity` / `is_adult_activity` posés par l'admin.
 */

export type MembershipCategory = 'adult' | 'child';

/** Borne basse du champ `date_naissance` (`min="1900-01-01"` dans l'étape 2). */
const MIN_YEAR = 1900;

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Âge en années révolues, ou `null` si la date est absente, mal formée,
 * inexistante au calendrier ou hors des bornes du formulaire.
 *
 * Le calcul compare les dates civiles au lieu de diviser un nombre de jours :
 * `days // 365` (ce que fait `crud.get_dashboard_stats`) avance d'un jour tous
 * les 4 ans et peut faire basculer trop tôt un adhérent pile sur le seuil.
 */
export function ageAt(dateNaissance: string | null | undefined, reference: Date = new Date()): number | null {
  const match = ISO_DATE.exec(dateNaissance ?? '');
  if (!match) return null;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);

  // `new Date(2010, 1, 30)` ne lève pas : il roule sur le 2 mars. On ne garde
  // la date que si elle se relit à l'identique.
  const birth = new Date(year, month - 1, day);
  if (birth.getFullYear() !== year || birth.getMonth() !== month - 1 || birth.getDate() !== day) {
    return null;
  }

  if (year < MIN_YEAR || birth > reference) return null;

  const beforeBirthday =
    reference.getMonth() < month - 1 ||
    (reference.getMonth() === month - 1 && reference.getDate() < day);

  return reference.getFullYear() - year - (beforeBirthday ? 1 : 0);
}

/**
 * Catégorie d'adhésion pour une date de naissance, ou `null` si l'âge n'est pas
 * calculable — mieux vaut ne rien afficher que d'annoncer une catégorie fausse.
 *
 * Le seuil vient de `/api/config` (`adult_age_threshold`), il n'est pas en dur.
 */
export function membershipCategory(
  dateNaissance: string | null | undefined,
  threshold: number,
  reference: Date = new Date(),
): MembershipCategory | null {
  const age = ageAt(dateNaissance, reference);
  if (age === null) return null;
  return age < threshold ? 'child' : 'adult';
}

export function membershipLabel(category: MembershipCategory): string {
  return category === 'child' ? 'Adhésion Enfant' : 'Adhésion Adulte';
}
