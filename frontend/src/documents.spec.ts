import { describe, it, expect } from 'vitest';
import { hasDocument, documentUrl, documentsToSign } from './documents';
import type { Activity } from './types';

const activity = (over: Partial<Activity> = {}): Activity => ({
  id: 1,
  name: 'Gym',
  description: '',
  location: '',
  max_participants: 0,
  current_participants: 0,
  registration_deadline: null,
  day_of_week: null,
  start_time: null,
  end_time: null,
  is_child_activity: false,
  is_adult_activity: true,
  resident_price: 100,
  external_price: 120,
  document_filename: null,
  ...over,
});

describe('hasDocument', () => {
  it('est vrai quand un nom de document est présent', () => {
    expect(hasDocument(activity({ document_filename: 'reglement.pdf' }))).toBe(true);
  });

  it('est faux quand le champ est nul', () => {
    expect(hasDocument(activity())).toBe(false);
  });

  it('est faux quand le champ est une chaîne vide', () => {
    expect(hasDocument(activity({ document_filename: '' }))).toBe(false);
  });
});

describe('documentUrl', () => {
  it("dérive l'URL de l'id de l'activité", () => {
    expect(documentUrl(activity({ id: 7 }))).toBe('/api/activities/7/document');
  });
});

describe('documentsToSign', () => {
  it('ne garde que les activités qui exigent un document', () => {
    const result = documentsToSign([
      activity({ id: 1, name: 'Gym', document_filename: 'reglement.pdf' }),
      activity({ id: 2, name: 'Danse' }),
      activity({ id: 3, name: 'Judo', document_filename: 'certificat.pdf' }),
    ]);

    expect(result.map((a) => a.name)).toEqual(['Gym', 'Judo']);
  });

  it('renvoie une liste vide pour une sélection sans document', () => {
    expect(documentsToSign([activity()])).toEqual([]);
  });

  it('tolère une liste vide', () => {
    expect(documentsToSign([])).toEqual([]);
  });
});
