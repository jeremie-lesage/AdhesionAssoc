import { describe, it, expect, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useFormStore } from './form'
import type { Activity } from '@/types'

/**
 * Seul l'`id` compte pour ces tests : les fusionner avec une activité complète
 * n'ajouterait rien et masquerait ce qui est vérifié.
 */
const activity = (id: number) => ({ id }) as Activity

describe('useFormStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('navigation entre les étapes', () => {
    it('démarre à l’étape 1', () => {
      expect(useFormStore().step).toBe(1)
    })

    it('avance jusqu’à l’étape 4 et s’y arrête', () => {
      const store = useFormStore()

      for (let i = 0; i < 10; i++) store.nextStep()

      expect(store.step).toBe(4)
    })

    it('recule jusqu’à l’étape 1 et s’y arrête', () => {
      const store = useFormStore()
      store.step = 3

      for (let i = 0; i < 10; i++) store.prevStep()

      expect(store.step).toBe(1)
    })
  })

  describe('setFormData', () => {
    it('fusionne les champs fournis sans écraser les autres', () => {
      const store = useFormStore()
      store.setFormData({ email: 'jean@example.com' })

      store.setFormData({ nom: 'Dupont' })

      expect(store.formData.email).toBe('jean@example.com')
      expect(store.formData.nom).toBe('Dupont')
    })

    it('remplace la liste d’activités au lieu de la fusionner', () => {
      const store = useFormStore()
      store.setFormData({ activities: [activity(1), activity(2)] })

      store.setFormData({ activities: [activity(3)] })

      expect(store.formData.activities).toEqual([{ id: 3 }])
    })
  })

  describe('resetForm', () => {
    it('remet le formulaire et le code généré à zéro', () => {
      const store = useFormStore()
      store.setFormData({ email: 'jean@example.com', ville: 'Fauverney' })
      store.lastGeneratedCode = 'ABCDEF123456'
      store.step = 4

      store.resetForm()

      expect(store.step).toBe(1)
      expect(store.formData.email).toBe('')
      expect(store.formData.activities).toEqual([])
      expect(store.formData.status).toBe('pending')
      expect(store.lastGeneratedCode).toBeNull()
    })
  })

  describe('setFormDataForEdit', () => {
    it('repart d’un état vierge avant d’appliquer les données chargées', () => {
      const store = useFormStore()
      store.setFormData({ telephone: '0102030405' })
      store.step = 3

      store.setFormDataForEdit({ email: 'charge@example.com', code: 'CODE12345678' })

      expect(store.step).toBe(1)
      expect(store.formData.telephone).toBe('')
      expect(store.formData.email).toBe('charge@example.com')
      expect(store.formData.code).toBe('CODE12345678')
    })
  })
})
