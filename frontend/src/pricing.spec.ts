import { describe, it, expect } from 'vitest';
import { isResident, activityPrice, activitiesCost, adhesionTotal } from './pricing';

const yoga = { resident_price: 100, external_price: 120 };
const danse = { resident_price: 80, external_price: 95 };

describe('isResident', () => {
  it('reconnaît la commune du foyer rural', () => {
    expect(isResident('Fauverney')).toBe(true);
  });

  it('ignore la casse', () => {
    expect(isResident('FAUVERNEY')).toBe(true);
    expect(isResident('fauverney')).toBe(true);
  });

  it('refuse une autre commune', () => {
    expect(isResident('Dijon')).toBe(false);
  });

  it('traite une ville absente comme non résidente', () => {
    expect(isResident('')).toBe(false);
    expect(isResident(null)).toBe(false);
    expect(isResident(undefined)).toBe(false);
  });

  // TODO(règle métier) — cas limites non tranchés : voir le commentaire en fin de
  // fichier. `isResident('Fauverney ')` renvoie aujourd'hui `false`, donc le tarif
  // extérieur, sur une simple espace en fin de saisie.
});

describe('activityPrice', () => {
  it('applique le tarif résident à un habitant de Fauverney', () => {
    expect(activityPrice(yoga, 'Fauverney')).toBe(100);
  });

  it('applique le tarif extérieur aux autres', () => {
    expect(activityPrice(yoga, 'Dijon')).toBe(120);
  });

  it('renvoie undefined quand le tarif n’est pas renseigné', () => {
    const sansTarif = { resident_price: undefined, external_price: undefined };

    expect(activityPrice(sansTarif, 'Fauverney')).toBeUndefined();
  });

  it('distingue un tarif gratuit d’un tarif absent', () => {
    const gratuit = { resident_price: 0, external_price: 50 };

    expect(activityPrice(gratuit, 'Fauverney')).toBe(0);
  });
});

describe('activitiesCost', () => {
  it('somme les tarifs des activités', () => {
    expect(activitiesCost([yoga, danse], 'Fauverney')).toBe(180);
    expect(activitiesCost([yoga, danse], 'Dijon')).toBe(215);
  });

  it('vaut 0 sans activité', () => {
    expect(activitiesCost([], 'Fauverney')).toBe(0);
  });

  it('compte un tarif manquant pour 0 au lieu de produire NaN', () => {
    const sansTarif = { resident_price: undefined, external_price: undefined };

    expect(activitiesCost([yoga, sansTarif], 'Fauverney')).toBe(100);
  });
});

describe('adhesionTotal', () => {
  it('additionne adhésion et activités', () => {
    const total = adhesionTotal({
      ville: 'Fauverney',
      activities: [yoga],
      adhesion_amount: 15,
    });

    expect(total).toBe(115);
  });

  it('déduit la réduction', () => {
    const total = adhesionTotal({
      ville: 'Fauverney',
      activities: [yoga],
      adhesion_amount: 15,
      discount_amount: 20,
    });

    expect(total).toBe(95);
  });

  it('ne descend jamais sous zéro, même si la réduction dépasse le dû', () => {
    const total = adhesionTotal({
      ville: 'Fauverney',
      activities: [yoga],
      adhesion_amount: 15,
      discount_amount: 500,
    });

    expect(total).toBe(0);
  });

  it('tolère des montants absents', () => {
    const total = adhesionTotal({ ville: 'Dijon', activities: [danse] });

    expect(total).toBe(95);
  });
});

// ─── À compléter : politique de normalisation de la ville ──────────────────────
//
// `isResident` compare `ville.toLowerCase()` à 'fauverney', sans normalisation.
// Conséquences aujourd'hui, toutes facturées au tarif extérieur :
//   isResident('Fauverney ')   → false  (espace de fin, saisie manuelle)
//   isResident(' Fauverney')   → false
//   isResident('Fauverney\t')  → false
//
// La ville vient soit de l'autocomplétion geo.api.gouv.fr, soit d'une saisie
// libre. Le choix de la règle a un effet direct sur le montant facturé, donc
// c'est une décision métier, pas technique :
//   - trim() seulement : corrige les espaces, reste strict sur l'orthographe
//   - trim() + suppression des accents/tirets : plus permissif, mais rendrait
//     'Fauverney-le-Bas' résident si une telle commune existait
//   - aucune normalisation : on considère que l'autocomplétion garantit la valeur
//
// Ajouter les cas voulus dans le `describe('isResident')` ci-dessus, puis ajuster
// `isResident` dans pricing.ts en conséquence.
