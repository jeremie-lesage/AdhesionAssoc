<template>
  <div class="public-view">
    <h2>Charger un formulaire existant</h2>
    <form @submit.prevent="loadForm">
      <div>
        <label for="code">Votre code d'accès:</label>
        <input type="text" id="code" v-model="code" required>
      </div>
      <button type="submit">Charger</button>
    </form>

    <div v-if="families.length > 0" class="families">
      <h3>Vos inscriptions</h3>
      <div v-for="family in families" :key="family.email" class="family-card">
        <div class="family-header">
          <span class="family-email">{{ family.email }}</span>
          <span class="family-address">{{ familyAddress(family) }}</span>
        </div>
        <ul class="family-members">
          <li v-for="member in family.members" :key="member.code">
            <a href="#" @click.prevent="useCode(member.code)">
              {{ member.prenom }} {{ member.nom }}
            </a>
            <span class="member-code">{{ member.code }}</span>
            <span class="member-status" :class="`status-${member.status}`">
              {{ statusLabel(member.status) }}
            </span>
          </li>
        </ul>
        <button type="button" class="add-member" @click="addMember(family)">
          Ajouter un membre dans cette famille
        </button>
      </div>
    </div>

    <MessageModal
      :visible="modal.visible"
      :title="modal.title"
      :message="modal.message"
      :variant="modal.variant"
      @close="modal.visible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getAdhesionByCode } from '@/api';
import type { Adhesion } from '@/types';
import { groupByFamily, readRecentCodes, type Family } from '@/family';
import MessageModal from '@/components/MessageModal.vue';

const router = useRouter();
const code = ref('');
const families = ref<Family[]>([]);

const modal = ref<{
  visible: boolean;
  title: string;
  message: string;
  variant: 'info' | 'warning' | 'error';
}>({ visible: false, title: '', message: '', variant: 'info' });

const showModal = (title: string, message: string, variant: 'info' | 'warning' | 'error') => {
  modal.value = { visible: true, title, message, variant };
};

onMounted(async () => {
  const results = await Promise.all(
    readRecentCodes().map(async (recentCode) => {
      try {
        return await getAdhesionByCode(recentCode);
      } catch (error) {
        // Code périmé ou adhésion supprimée : on l'ignore plutôt que de vider la liste.
        console.error(`Impossible de charger les détails pour le code ${recentCode}`, error);
        return null;
      }
    })
  );

  families.value = groupByFamily(results.filter((a): a is Adhesion => a !== null));
});

const familyAddress = (family: Family) => {
  const { nom_rue, code_postal, ville } = family.reference;
  return [nom_rue, [code_postal, ville].filter(Boolean).join(' ')].filter(Boolean).join(' — ');
};

const statusLabel = (status: string) => {
  switch (status) {
    case 'pending': return 'En attente';
    case 'validated': return 'Validée';
    case 'paid': return 'Payée';
    default: return status;
  }
};

const useCode = (selectedCode: string) => {
  code.value = selectedCode;
};

/**
 * Le code passé est celui du membre de référence : c'est de lui que le formulaire
 * recopiera email, téléphone et adresse. Il ne sera pas modifié pour autant —
 * l'étape 4 fera bien un POST.
 */
const addMember = (family: Family) => {
  router.push({ name: 'adhesion', query: { family: family.reference.code } });
};

const loadForm = async () => {
  if (!code.value) return;
  try {
    const adhesion = await getAdhesionByCode(code.value);
    if (adhesion.status === 'validated' || adhesion.status === 'paid') {
      showModal(
        'Inscription déjà finalisée',
        'Ce formulaire a déjà été finalisé et ne peut plus être modifié.\n'
          + 'Pour toute correction, contactez un responsable du Foyer Rural.',
        'warning'
      );
      return;
    }
    router.push({ name: 'adhesion', query: { code: code.value } });
  } catch (error) {
    console.error(error);
    showModal(
      'Code introuvable',
      'Code invalide ou formulaire non trouvé.\nVérifiez le code reçu par email.',
      'error'
    );
  }
};
</script>

<style scoped>
.families {
  margin-top: 2rem;
}

.family-card {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.family-header {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  margin-bottom: 0.75rem;
}

.family-email {
  font-weight: 600;
  color: var(--color-text);
}

.family-address {
  font-size: 0.85rem;
  color: #777;
}

.family-members {
  list-style: none;
  padding: 0;
  margin: 0 0 0.75rem;
}

.family-members li {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.35rem 0;
  border-top: 1px solid var(--color-border);
}

.family-members a {
  text-decoration: none;
  color: var(--color-primary);
  cursor: pointer;
  font-weight: bold;
}

.family-members a:hover {
  text-decoration: underline;
}

.member-code {
  font-family: monospace;
  font-size: 0.8rem;
  color: #777;
}

.member-status {
  margin-left: auto;
  padding: 0.1rem 0.5rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-pending {
  background: #fff3cd;
  color: #8a6d3b;
}

.status-validated {
  background: #e3f2fd;
  color: #1565c0;
}

.status-paid {
  background: #e8f5e9;
  color: #2e7d32;
}

.add-member {
  width: 100%;
}
</style>
