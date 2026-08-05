import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ageAt, membershipCategory, membershipLabel } from './age';

// L'âge dépend de « aujourd'hui » : sans horloge figée ces tests changeraient
// de résultat au fil des jours.
beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date(2026, 7, 5)); // 5 août 2026
});

afterEach(() => {
  vi.useRealTimers();
});

describe('ageAt', () => {
  it('compte les années révolues', () => {
    expect(ageAt('2000-08-05')).toBe(26);
    expect(ageAt('2010-01-01')).toBe(16);
  });

  it('n’ajoute l’année qu’à partir du jour anniversaire', () => {
    expect(ageAt('2010-08-04')).toBe(16); // anniversaire passé d'un jour
    expect(ageAt('2010-08-05')).toBe(16); // anniversaire aujourd'hui
    expect(ageAt('2010-08-06')).toBe(15); // anniversaire demain
  });

  it('ne dérive pas sur les années bissextiles', () => {
    // Le backend fait `days // 365`, qui perd un jour tous les 4 ans.
    // Un enfant né le 5 août 2010 a 16 ans jour pour jour, pas 16 ans et 4 jours.
    expect(ageAt('1900-08-05')).toBe(126);
  });

  it('rejette une date absente, vide ou mal formée', () => {
    expect(ageAt('')).toBeNull();
    expect(ageAt('05/08/2010')).toBeNull();
    expect(ageAt('2010-08')).toBeNull();
  });

  it('rejette une date inexistante au calendrier', () => {
    // `new Date(2010, 1, 30)` roulerait sur le 2 mars sans contrôle.
    expect(ageAt('2010-02-30')).toBeNull();
    expect(ageAt('2010-13-01')).toBeNull();
  });

  it('rejette une date hors des bornes du formulaire', () => {
    expect(ageAt('1899-12-31')).toBeNull(); // avant le min="1900-01-01"
    expect(ageAt('2026-08-06')).toBeNull(); // dans le futur
  });
});

describe('membershipCategory', () => {
  it('classe selon le seuil, borne incluse côté adulte', () => {
    expect(membershipCategory('2010-01-01', 16)).toBe('adult'); // 16 ans
    expect(membershipCategory('2011-01-01', 16)).toBe('child'); // 15 ans
  });

  it('suit le seuil fourni plutôt qu’une valeur en dur', () => {
    expect(membershipCategory('2010-01-01', 18)).toBe('child'); // 16 ans, seuil 18
  });

  it('ne classe pas une date inutilisable', () => {
    // Le backend compte ces cas comme adultes pour ses compteurs ; côté
    // formulaire mieux vaut ne rien annoncer que d'annoncer à tort.
    expect(membershipCategory('', 16)).toBeNull();
    expect(membershipCategory('2010-02-30', 16)).toBeNull();
  });
});

describe('membershipLabel', () => {
  it('donne le libellé affiché à l’adhérent', () => {
    expect(membershipLabel('adult')).toBe('Adhésion Adulte');
    expect(membershipLabel('child')).toBe('Adhésion Enfant');
  });
});
