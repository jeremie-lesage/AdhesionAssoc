import { describe, it, expect } from 'vitest';
import { DAY_LABELS, dayAndTime, dayLabel, formatSchedule, groupByDay } from './schedule';
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

describe('DAY_LABELS', () => {
  it('indexe les jours comme day_of_week, lundi en 0', () => {
    expect(DAY_LABELS[0]).toBe('Lundi');
    expect(DAY_LABELS[6]).toBe('Dimanche');
    expect(DAY_LABELS).toHaveLength(7);
  });
});

describe('dayLabel', () => {
  it('traduit le jour de la semaine', () => {
    expect(dayLabel(activity({ day_of_week: 3 }))).toBe('Jeudi');
  });

  it('vaut null quand aucun jour est renseigné', () => {
    expect(dayLabel(activity())).toBeNull();
  });

  it('vaut null sur un index hors bornes plutôt que undefined', () => {
    expect(dayLabel(activity({ day_of_week: 9 }))).toBeNull();
  });
});

describe('formatSchedule', () => {
  it('formate une plage horaire à la française', () => {
    expect(formatSchedule(activity({ start_time: '17:00:00', end_time: '18:30:00' })))
      .toBe('17h00 – 18h30');
  });

  it("accepte l'heure sans les secondes", () => {
    expect(formatSchedule(activity({ start_time: '09:15', end_time: '10:45' })))
      .toBe('09h15 – 10h45');
  });

  it("n'affiche que le début quand la fin manque", () => {
    expect(formatSchedule(activity({ start_time: '20:00:00' }))).toBe('20h00');
  });

  it('vaut null sans heure de début', () => {
    expect(formatSchedule(activity({ end_time: '18:00:00' }))).toBeNull();
  });
});

describe('dayAndTime', () => {
  it('assemble le jour et la plage horaire', () => {
    expect(dayAndTime(activity({ day_of_week: 0, start_time: '17:00:00', end_time: '18:30:00' })))
      .toBe('Lundi 17h00 – 18h30');
  });

  it('donne le jour seul quand aucune heure n’est saisie', () => {
    expect(dayAndTime(activity({ day_of_week: 2 }))).toBe('Mercredi');
  });

  it('donne l’horaire seul quand le jour manque', () => {
    // Une activité peut n'avoir qu'un créneau connu : mieux vaut l'afficher
    // que taire l'information parce que le jour n'est pas renseigné.
    expect(dayAndTime(activity({ start_time: '20:00:00' }))).toBe('20h00');
  });

  it('vaut null quand ni le jour ni l’heure ne sont connus', () => {
    expect(dayAndTime(activity())).toBeNull();
  });

  it('ignore un jour hors bornes comme le fait dayLabel', () => {
    expect(dayAndTime(activity({ day_of_week: 9, start_time: '10:00' }))).toBe('10h00');
  });
});

describe('groupByDay', () => {
  it('regroupe par jour et trie les jours dans l’ordre de la semaine', () => {
    const jeudi = activity({ id: 1, day_of_week: 3 });
    const lundi = activity({ id: 2, day_of_week: 0 });
    const groups = groupByDay([jeudi, lundi]);

    expect(groups.map((g) => g.label)).toEqual(['Lundi', 'Jeudi']);
    expect(groups[0].activities.map((a) => a.id)).toEqual([2]);
  });

  it('trie les activités d’un même jour par heure de début', () => {
    const tard = activity({ id: 1, day_of_week: 3, start_time: '18:00:00' });
    const tot = activity({ id: 2, day_of_week: 3, start_time: '17:00:00' });
    const groups = groupByDay([tard, tot]);

    expect(groups).toHaveLength(1);
    expect(groups[0].activities.map((a) => a.id)).toEqual([2, 1]);
  });

  it('place les activités sans heure après celles qui en ont, dans leur jour', () => {
    const sansHeure = activity({ id: 1, day_of_week: 3 });
    const avecHeure = activity({ id: 2, day_of_week: 3, start_time: '18:00:00' });
    const groups = groupByDay([sansHeure, avecHeure]);

    expect(groups[0].activities.map((a) => a.id)).toEqual([2, 1]);
  });

  it('rassemble les activités sans jour dans un dernier groupe nommé', () => {
    const groups = groupByDay([activity({ id: 1 }), activity({ id: 2, day_of_week: 3 })]);

    expect(groups.map((g) => g.label)).toEqual(['Jeudi', 'Horaire à préciser']);
    expect(groups[1].activities.map((a) => a.id)).toEqual([1]);
  });

  it('rend un groupe unique sans libellé quand aucune activité n’a de jour', () => {
    const groups = groupByDay([activity({ id: 1 }), activity({ id: 2 })]);

    expect(groups).toHaveLength(1);
    expect(groups[0].label).toBeNull();
    expect(groups[0].activities.map((a) => a.id)).toEqual([1, 2]);
  });

  it('ne rend aucun groupe pour une liste vide', () => {
    expect(groupByDay([])).toEqual([]);
  });

  it('donne à chaque groupe une clé stable et distincte', () => {
    const groups = groupByDay([activity({ id: 1 }), activity({ id: 2, day_of_week: 3 })]);

    expect(new Set(groups.map((g) => g.key)).size).toBe(2);
  });

  it('ne modifie pas le tableau reçu', () => {
    const input = [activity({ id: 1, day_of_week: 3 }), activity({ id: 2, day_of_week: 0 })];
    groupByDay(input);

    expect(input.map((a) => a.id)).toEqual([1, 2]);
  });
});
