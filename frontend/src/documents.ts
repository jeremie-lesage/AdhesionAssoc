import type { Activity } from '@/types';

/**
 * Règles d'affichage des documents à remplir et signer.
 *
 * Même parti pris que `pricing.ts` : la logique vit ici, en fonctions pures
 * testables, et les composants ne font que l'afficher. Trois vues la partagent
 * (choix des activités, résumé, modale de confirmation) et l'auraient sinon
 * dupliquée.
 */

/** Une activité exige un document dès qu'un nom de fichier est enregistré. */
export const hasDocument = (activity: Activity): boolean =>
  Boolean(activity.document_filename);

/** L'URL se dérive de l'id : le nom de fichier n'est qu'un libellé. */
export const documentUrl = (activity: Activity): string =>
  `/api/activities/${activity.id}/document`;

/** Les activités de cette sélection qui demandent un document signé. */
export const documentsToSign = (activities: Activity[]): Activity[] =>
  activities.filter(hasDocument);
