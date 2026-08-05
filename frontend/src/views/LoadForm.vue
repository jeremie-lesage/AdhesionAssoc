<template>
  <div class="public-view">
    <h2>Vos demandes d'inscription</h2>

    <!-- Les familles d'abord : c'est le chemin courant (« j'inscris un proche de
         plus »). La saisie manuelle du code sert au cas où — autre appareil,
         navigateur nettoyé — et passe donc après. -->
    <div v-if="families.length > 0" class="families">
      <div v-for="family in families" :key="family.email" class="family-card">
        <div class="family-header">
          <span class="family-email">{{ family.email }}</span>
          <span class="family-address">{{ familyAddress(family) }}</span>
        </div>
        <ul class="family-members">
          <li v-for="member in family.members" :key="member.code">
            <a href="#" @click.prevent="openAdhesion(member.code)">
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

    <p v-else class="hint">
      Aucune inscription enregistrée sur cet appareil.
    </p>

    <div class="load-by-code" :class="{ separated: families.length > 0 }">
      <h3>Charger un formulaire avec son code</h3>
      <p class="hint">
        Utile depuis un autre appareil ou après un nettoyage du navigateur : le code
        d'accès vous a été communiqué à la fin du formulaire.
      </p>
      <form @submit.prevent="loadForm">
        <div>
          <label for="code">Votre code d'accès:</label>
          <input type="text" id="code" v-model="code" required>
        </div>
        <button type="submit">Charger</button>
      </form>
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

/**
 * Le code passé est celui du membre de référence : c'est de lui que le formulaire
 * recopiera email, téléphone et adresse. Il ne sera pas modifié pour autant —
 * l'étape 4 fera bien un POST.
 */
const addMember = (family: Family) => {
  router.push({ name: 'adhesion', query: { family: family.reference.code } });
};

/**
 * Ouvre le formulaire d'une adhésion, qu'on arrive par un clic sur un membre ou
 * par la saisie du code : le contrôle du statut vaut dans les deux cas.
 */
const openAdhesion = async (targetCode: string) => {
  if (!targetCode) return;
  try {
    const adhesion = await getAdhesionByCode(targetCode);
    if (adhesion.status === 'validated' || adhesion.status === 'paid') {
      showModal(
        'Inscription déjà finalisée',
        'Ce formulaire a déjà été finalisé et ne peut plus être modifié.\n'
          + 'Pour toute correction, contactez un responsable du Foyer Rural.',
        'warning'
      );
      return;
    }
    router.push({ name: 'adhesion', query: { code: targetCode } });
  } catch (error) {
    console.error(error);
    showModal(
      'Code introuvable',
      'Code invalide ou formulaire non trouvé.\nVérifiez le code reçu par email.',
      'error'
    );
  }
};

const loadForm = () => openAdhesion(code.value);
</script>

<style scoped>
.load-by-code {
  margin-top: 1.5rem;
}

/* Trait de séparation seulement s'il y a bien une liste au-dessus. */
.load-by-code.separated {
  margin-top: 2.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

.load-by-code h3 {
  margin-top: 0;
}

.hint {
  font-size: 0.85rem;
  color: #777;
  margin-top: -0.5rem;
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
