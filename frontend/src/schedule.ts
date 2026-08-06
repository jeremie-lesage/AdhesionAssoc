import type { Activity } from '@/types';

/**
 * Règles d'affichage des créneaux horaires des activités.
 *
 * Même parti pris que `pricing.ts` et `documents.ts` : la logique vit ici, en
 * fonctions pures testables, et les composants ne font que l'afficher. Le
 * regroupement par jour du formulaire et l'agenda hebdomadaire partagent au
 * moins les libellés de jours, qui étaient dupliqués dans trois vues.
 */

/** Libellés indexés comme `activities.day_of_week` : lundi vaut 0. */
export const DAY_LABELS = [
  'Lundi',
  'Mardi',
  'Mercredi',
  'Jeudi',
  'Vendredi',
  'Samedi',
  'Dimanche',
] as const;

/** Titre du groupe rassemblant les activités dont le jour n'est pas saisi. */
const UNDATED_LABEL = 'Horaire à préciser';

const UNDATED_KEY = 'undated';

/**
 * Le jour de l'activité, ou `null` si le champ est vide — ou hors bornes, un
 * `day_of_week` aberrant valant mieux traité comme une absence de jour qu'affiché
 * en `undefined`.
 */
export const dayLabel = (activity: Activity): string | null => {
  if (activity.day_of_week == null) return null;
  return DAY_LABELS[activity.day_of_week] ?? null;
};

/** `'18:00:00'` et `'18:00'` donnent tous deux `'18h00'`. */
const toFrenchTime = (time: string): string => {
  const [hours, minutes] = time.split(':');
  return `${hours}h${minutes ?? '00'}`;
};

/** `'17h00 – 18h30'`, ou la seule heure de début si la fin manque. */
export const formatSchedule = (activity: Activity): string | null => {
  if (!activity.start_time) return null;
  const start = toFrenchTime(activity.start_time);
  if (!activity.end_time) return start;
  return `${start} – ${toFrenchTime(activity.end_time)}`;
};

/**
 * `'Lundi 17h00 – 18h30'`, ou la seule partie connue, ou `null` si le créneau
 * est entièrement vide.
 *
 * Utile là où les activités ne sont **pas** groupées par jour (l'accueil) : dans
 * `Etape3_Activites` le jour est déjà porté par l'intertitre du groupe, il n'y a
 * que `formatSchedule` à afficher.
 */
export const dayAndTime = (activity: Activity): string | null => {
  const parts = [dayLabel(activity), formatSchedule(activity)].filter(Boolean);
  return parts.length ? parts.join(' ') : null;
};

export interface DayGroup {
  /** Clé stable pour le `v-for`. */
  key: string;
  /**
   * Titre du groupe, ou `null` quand aucune activité n'a de jour : dans ce cas
   * un seul groupe est rendu et l'afficher sous un intertitre solitaire
   * n'apprendrait rien au lecteur.
   */
  label: string | null;
  activities: Activity[];
}

/** Les créneaux vides passent en fin de journée, faute de savoir où les placer. */
const byStartTime = (a: Activity, b: Activity): number => {
  if (!a.start_time) return b.start_time ? 1 : 0;
  if (!b.start_time) return -1;
  return a.start_time.localeCompare(b.start_time);
};

/**
 * Répartit les activités par jour, dans l'ordre de la semaine puis de l'heure,
 * les activités sans jour formant un dernier groupe. N'altère pas l'entrée.
 */
export const groupByDay = (activities: Activity[]): DayGroup[] => {
  const dated = new Map<number, Activity[]>();
  const undated: Activity[] = [];

  for (const activity of activities) {
    if (dayLabel(activity) === null) {
      undated.push(activity);
      continue;
    }
    const day = activity.day_of_week as number;
    const bucket = dated.get(day);
    if (bucket) bucket.push(activity);
    else dated.set(day, [activity]);
  }

  if (dated.size === 0) {
    return undated.length ? [{ key: UNDATED_KEY, label: null, activities: undated }] : [];
  }

  const groups: DayGroup[] = [...dated.keys()]
    .sort((a, b) => a - b)
    .map((day) => ({
      key: `day-${day}`,
      label: DAY_LABELS[day],
      activities: dated.get(day)!.sort(byStartTime),
    }));

  if (undated.length) {
    groups.push({ key: UNDATED_KEY, label: UNDATED_LABEL, activities: undated });
  }

  return groups;
};
