import { describe, it, expect, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createRouter, createMemoryHistory, type Router } from 'vue-router';
import { createPinia, setActivePinia } from 'pinia';
import App from './App.vue';

// Routes minimales : App n'a besoin que des chemins vers lesquels sa nav pointe.
// Charger les vraies vues déclencherait leurs appels API au montage.
const Stub = { template: '<div />' };

const makeRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: Stub },
      { path: '/adhesion', component: Stub },
      { path: '/planning', component: Stub },
      { path: '/load', component: Stub },
      { path: '/admin', component: Stub },
      { path: '/admin/dashboard', component: Stub },
    ],
  });

const mountAt = async (router: Router, path: string) => {
  await router.push(path);
  await router.isReady();
  return mount(App, { global: { plugins: [router] } });
};

describe('App — navigation publique', () => {
  let router: Router;

  beforeEach(() => {
    setActivePinia(createPinia());
    router = makeRouter();
  });

  it('n’affiche pas de lien « Accueil » quand on est déjà sur l’accueil', async () => {
    const wrapper = await mountAt(router, '/');

    const labels = wrapper.findAll('#site-menu li').map((li) => li.text());
    expect(labels).not.toContain('Accueil');
    // Pas de « Nouveau Formulaire » : l'inscription démarre depuis le bouton
    // « S'inscrire » de l'accueil, pas depuis la nav.
    expect(labels).toEqual([
      'Planning',
      'Reprendre mon inscription',
      'Administration',
    ]);
  });

  it('affiche le lien « Accueil » sur les autres pages publiques', async () => {
    const wrapper = await mountAt(router, '/planning');

    expect(wrapper.findAll('#site-menu li').map((li) => li.text())).toContain('Accueil');
  });

  it('garde toutes les entrées dans le DOM, le repli mobile étant purement CSS', async () => {
    const wrapper = await mountAt(router, '/');

    // Le menu doit rester atteignable : la régression corrigée était un
    // display:none sans déclencheur, qui rendait ces entrées inaccessibles.
    expect(wrapper.find('#site-menu').exists()).toBe(true);
    expect(wrapper.find('.nav-toggle').attributes('aria-controls')).toBe('site-menu');
  });

  it('ouvre et referme le menu au clic sur le bouton', async () => {
    const wrapper = await mountAt(router, '/');
    const toggle = wrapper.find('.nav-toggle');

    expect(toggle.attributes('aria-expanded')).toBe('false');
    expect(wrapper.find('#site-menu').classes()).not.toContain('open');

    await toggle.trigger('click');
    expect(toggle.attributes('aria-expanded')).toBe('true');
    expect(wrapper.find('#site-menu').classes()).toContain('open');

    await toggle.trigger('click');
    expect(wrapper.find('#site-menu').classes()).not.toContain('open');
  });

  it('referme le menu après une navigation', async () => {
    const wrapper = await mountAt(router, '/');

    await wrapper.find('.nav-toggle').trigger('click');
    expect(wrapper.find('#site-menu').classes()).toContain('open');

    await router.push('/load');
    await wrapper.vm.$nextTick();

    expect(wrapper.find('#site-menu').classes()).not.toContain('open');
  });

  it('masque toute la nav publique sur les routes admin', async () => {
    const wrapper = await mountAt(router, '/admin/dashboard');

    expect(wrapper.find('nav').exists()).toBe(false);
  });
});
