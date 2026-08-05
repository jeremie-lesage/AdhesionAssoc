import { describe, it, expect, beforeEach } from 'vitest';
import {
  MAX_RECENT_CODES,
  familyContact,
  familyKey,
  groupByFamily,
  readRecentCodes,
  referenceMember,
  rememberCode,
} from './family';
import type { Adhesion } from './types';

/**
 * Seuls `id`, `email` et les coordonnées comptent ici : compléter l'adhésion
 * masquerait ce qui est réellement vérifié.
 */
const adhesion = (over: Partial<Adhesion> = {}): Adhesion => ({
  id: 1,
  code: 'CODE00000001',
  email: 'famille@example.com',
  telephone: '0102030405',
  nom: 'DUPONT',
  prenom: 'Jean',
  date_naissance: '1980-01-01',
  nom_rue: '1 rue des Lilas',
  code_postal: '21110',
  ville: 'Fauverney',
  adhesion_amount: 12,
  activities: [],
  discount_amount: 0,
  discount_reason: null,
  status: 'pending',
  email_sent_at: null,
  submission_email_sent_at: null,
  ...over,
});

describe('familyKey', () => {
  it('normalise la casse et les espaces', () => {
    expect(familyKey('  Jean@Example.COM ')).toBe('jean@example.com');
  });
});

describe('groupByFamily', () => {
  it('regroupe les adhésions partageant la même adresse email', () => {
    const families = groupByFamily([
      adhesion({ id: 1, code: 'A', email: 'famille@example.com' }),
      adhesion({ id: 2, code: 'B', email: 'autre@example.com' }),
      adhesion({ id: 3, code: 'C', email: 'famille@example.com' }),
    ]);

    expect(families).toHaveLength(2);
    expect(families[0].email).toBe('famille@example.com');
    expect(families[0].members.map(m => m.code)).toEqual(['A', 'C']);
    expect(families[1].members.map(m => m.code)).toEqual(['B']);
  });

  it('ignore la casse de l’email pour le regroupement', () => {
    const families = groupByFamily([
      adhesion({ id: 1, code: 'A', email: 'Famille@Example.com' }),
      adhesion({ id: 2, code: 'B', email: 'famille@example.com' }),
    ]);

    expect(families).toHaveLength(1);
    expect(families[0].members).toHaveLength(2);
  });

  it('trie les membres par ordre de création', () => {
    const families = groupByFamily([
      adhesion({ id: 9, code: 'DERNIER' }),
      adhesion({ id: 2, code: 'PREMIER' }),
      adhesion({ id: 5, code: 'MILIEU' }),
    ]);

    expect(families[0].members.map(m => m.code)).toEqual(['PREMIER', 'MILIEU', 'DERNIER']);
  });

  it('prend le premier membre créé comme référence, quel que soit l’ordre d’entrée', () => {
    const families = groupByFamily([
      adhesion({ id: 9, code: 'DERNIER', nom_rue: '9 rue Neuve' }),
      adhesion({ id: 2, code: 'PREMIER', nom_rue: '1 rue des Lilas' }),
    ]);

    expect(families[0].reference.code).toBe('PREMIER');
    expect(families[0].reference.nom_rue).toBe('1 rue des Lilas');
  });

  it('rend une liste vide sans adhésion', () => {
    expect(groupByFamily([])).toEqual([]);
  });
});

describe('referenceMember', () => {
  it('retient le plus petit id', () => {
    const first = adhesion({ id: 3, code: 'PREMIER' });

    expect(referenceMember([adhesion({ id: 8 }), first, adhesion({ id: 5 })])).toBe(first);
  });
});

describe('familyContact', () => {
  it('ne retient que les champs partagés par la famille', () => {
    expect(familyContact(adhesion({ nom: 'DUPONT', prenom: 'Jean' }))).toEqual({
      email: 'famille@example.com',
      telephone: '0102030405',
      nom_rue: '1 rue des Lilas',
      code_postal: '21110',
      ville: 'Fauverney',
    });
  });

  it('remplace les coordonnées absentes par une chaîne vide', () => {
    const contact = familyContact(adhesion({ telephone: null as unknown as string }));

    expect(contact.telephone).toBe('');
  });
});

describe('codes récents', () => {
  // `vitest.setup.ts` vide déjà le stockage avant chaque test ; ce reset explicite
  // garde le fichier lisible seul.
  beforeEach(() => {
    localStorage.clear();
  });

  it('rend une liste vide sans entrée mémorisée', () => {
    expect(readRecentCodes()).toEqual([]);
  });

  it('ajoute les codes les plus récents en tête', () => {
    rememberCode('AAA');
    rememberCode('BBB');

    expect(readRecentCodes()).toEqual(['BBB', 'AAA']);
  });

  it('remonte un code déjà présent sans le dupliquer', () => {
    rememberCode('AAA');
    rememberCode('BBB');
    rememberCode('AAA');

    expect(readRecentCodes()).toEqual(['AAA', 'BBB']);
  });

  it('tronque au-delà de la limite', () => {
    for (let i = 0; i < MAX_RECENT_CODES + 5; i++) rememberCode(`CODE${i}`);

    const codes = readRecentCodes();
    expect(codes).toHaveLength(MAX_RECENT_CODES);
    expect(codes[0]).toBe(`CODE${MAX_RECENT_CODES + 4}`);
  });

  it('repart de zéro sur une entrée corrompue', () => {
    localStorage.setItem('recentCodes', '{pas du json');

    expect(readRecentCodes()).toEqual([]);
  });

  it('dédoublonne une liste héritée de l’ancienne implémentation', () => {
    localStorage.setItem('recentCodes', JSON.stringify(['AAA', 'BBB', 'AAA']));

    expect(readRecentCodes()).toEqual(['AAA', 'BBB']);
  });

  it('écarte les entrées qui ne sont pas des chaînes', () => {
    localStorage.setItem('recentCodes', JSON.stringify(['AAA', 42, null]));

    expect(readRecentCodes()).toEqual(['AAA']);
  });
});
