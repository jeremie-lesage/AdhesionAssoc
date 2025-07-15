<template>
  <div>
    <h2>Administration des Adhésions</h2>
    <RouterLink class="button" to="/admin/activities">Gérer les Activités</RouterLink>
    <RouterLink class="button" to="/admin/adherents-by-activity">Adhérents par Activité</RouterLink>
    <RouterLink class="button" to="/admin/accounts">Gérer les comptes</RouterLink>
    <button :disabled="!adhesions.length" class="button export-button" @click="exportToCsv">Exporter toutes les
      adhésions en CSV
    </button>
    <p v-if="loading">Chargement des adhésions...</p>
    <p v-if="error">Erreur lors du chargement des adhésions: {{ error }}</p>
    <table v-if="adhesions.length">
      <thead>
      <tr>
        <th>Code</th>
        <th>Email</th>
        <th>Nom</th>
        <th>Prénom</th>
        <th>Adresse</th>
        <th>Montant Adhésion</th>
        <th>Activités</th>
        <th>Coût Total</th>
        <th>Statut</th>
        <th>Actions</th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="adhesion in adhesions" :key="adhesion.id!">
        <td>{{ adhesion.code }}</td>
        <td>{{ adhesion.email }}</td>
        <td>{{ adhesion.nom }}</td>
        <td>{{ adhesion.prenom }}</td>
        <td>{{ adhesion.numero_rue }}, {{ adhesion.nom_rue }} <br/> {{ adhesion.code_postal }} {{ adhesion.ville }}</td>
        <td>{{ adhesion.adhesion_amount }}€</td>
        <td>{{ adhesion.activites ? adhesion.activites.join(', ') : 'Aucune' }}</td>
        <td>{{ calculateTotalCost(adhesion) }}€</td>
        <td>{{ adhesion.status }}</td>
        <td>
          <button @click="editAdhesion(adhesion.code)">Corriger</button>
          <button v-if="adhesion.status === 'pending'" class="validate-button" @click="validateAdhesion(adhesion.code)">
            Valider
          </button>
          <button class="receipt-button" @click="generateReceiptPdf(adhesion)">Reçu</button>
        </td>
      </tr>
      </tbody>
    </table>
    <p v-else-if="!loading && !error">Aucune adhésion trouvée.</p>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, computed} from 'vue';
import {useRouter, RouterLink} from 'vue-router';
import {useFormStore} from '@/stores/form';
import api from '@/api';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import logoFoyerRural from '@/assets/images/logo_foyer_rural.png';
import type {Activity, Adhesion} from '@/types';

declare global {
  interface Window {
    BACKEND_URL: string;
  }
}

const adhesions = ref<Adhesion[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const router = useRouter();
const formStore = useFormStore();
const allActivities = ref<Activity[]>([]);

const fetchAdhesions = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.get('/api/adhesions');
    adhesions.value = response.data;
  } catch (err: any) {
    if (err.response && err.response.status === 401) {
      await router.push({name: 'admin-login'});
    } else {
      error.value = err.message;
    }
  } finally {
    loading.value = false;
  }
};

const fetchAllActivities = async () => {
  try {
    const response = await api.get('/api/activities');
    allActivities.value = response.data;
  } catch (err: any) {
    if (err.response && err.response.status === 401) {
      await router.push({name: 'admin-login'});
    } else {
      error.value = err.message;
    }
  }
};

const getPrice = (activity: Activity, city: string) => {
  if (city && city.toLowerCase() === 'fauverney') {
    return activity.resident_price;
  } else {
    return activity.external_price;
  }
};

const calculateTotalCost = (adhesion: Adhesion) => {
  let total = adhesion.adhesion_amount || 0;
  if (adhesion.activites && allActivities.value.length > 0) {
    adhesion.activites.forEach(adhesionActivityName => {
      const activity = allActivities.value.find(act => act.name === adhesionActivityName);
      if (activity) {
        total += getPrice(activity, adhesion.ville) || 0;
      }
    });
  }
  return total;
};

onMounted(() => {
  fetchAdhesions();
  fetchAllActivities();
});

const editAdhesion = async (code: string) => {
  try {
    const response = await api.get(`/api/adhesions/${code}`);
    formStore.formData = response.data;
    formStore.formData.code = response.data.code; // Assurez-vous que le code est bien stocké
    router.push('/adhesion'); // Redirige vers la page du formulaire
  } catch (err: any) {
    alert(`Impossible de charger le formulaire pour le code ${code}: ${err.message}`);
  }
};

const validateAdhesion = async (code: string) => {
  if (!confirm('Êtes-vous sûr de vouloir valider cette adhésion ?')) return;
  try {
    await api.put(`/api/adhesions/${code}/validate`);
    alert('Adhésion validée avec succès !');
    fetchAdhesions(); // Recharger la liste
  } catch (err: any) {
    alert(`Erreur lors de la validation de l'adhésion: ${err.response?.data?.detail || err.message}`);
  }
};

const exportToCsv = () => {
  if (!adhesions.value.length) return;

  const headers = [
    "Code", "Email", "Nom", "Prénom", "Numéro Rue", "Nom Rue",
    "Code Postal", "Ville", "Montant Adhésion", "Activités", "Statut", "Coût Total"
  ];
  const rows = adhesions.value.map(adhesion => [
    adhesion.code,
    adhesion.email,
    adhesion.nom,
    adhesion.prenom,
    adhesion.numero_rue,
    adhesion.nom_rue,
    adhesion.code_postal,
    adhesion.ville,
    adhesion.adhesion_amount,
    adhesion.activites ? adhesion.activites.join(', ') : 'Aucune',
    adhesion.status,
    calculateTotalCost(adhesion)
  ]);

  let csvContent = headers.join(";") + "\n";
  rows.forEach(row => {
    csvContent += row.join(";") + "\n";
  });

  const blob = new Blob([csvContent], {type: 'text/csv;charset=utf-8;'});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.setAttribute("download", "toutes_adhesions.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const generateReceiptPdf = async (adhesion: Adhesion) => {
  const receiptContent = `
    <div style="padding: 10mm; font-family: 'Arial', sans-serif; font-size: 10pt; margin: 0 auto; border: 1px solid #ccc;">
  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
  <tr>
  <td style="width: 50%; vertical-align: top;">
  <img src="${logoFoyerRural}" alt="Logo Foyer Rural" style="width: 40mm; height: auto;">
  <p style="margin: 5px 0;"><strong>Foyer Rural de Fauverney</strong></p>
  <p style="margin: 5px 0;">Rue Saint-Georges</p>
  <p style="margin: 5px 0;">21110 Fauverney</p>
  <p style="margin: 5px 0;">SIRET: 498 772 417 00016</p>
  <p style="margin: 5px 0;">Identifiant association: W212002406</p>
  </td>
  <td style="width: 50%; vertical-align: top; text-align: right;">
  <h1 style="color: #007bff; margin-bottom: 10px;">REÇU D'ADHÉSION</h1>
  <p style="margin: 5px 0;"><strong>Date:</strong> ${new Date().toLocaleDateString('fr-FR')}</p>
  <p style="margin: 5px 0;"><strong>N° Reçu:</strong> ${adhesion.code}-${new Date().getFullYear()}</p>
  </td>
  </tr>
  </table>

  <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #eee; background-color: #f9f9f9;">
  <p style="margin: 5px 0;"><strong>Adhérent:</strong> ${adhesion.prenom} ${adhesion.nom}</p>
  <p style="margin: 5px 0;"><strong>Email:</strong> ${adhesion.email}</p>
  <p style="margin: 5px 0;"><strong>Adresse:</strong> ${adhesion.numero_rue}, ${adhesion.nom_rue}</p>
  <p style="margin: 5px 0;">${adhesion.code_postal} ${adhesion.ville}</p>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
  <thead>
  <tr style="background-color: #007bff; color: white;">
  <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
  <th style="padding: 8px; border: 1px solid #ddd; text-align: right;">Montant (€)</th>
  </tr>
  </thead>
  <tbody>
  <tr>
  <td style="padding: 8px; border: 1px solid #ddd;">Adhésion</td>
  <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${adhesion.adhesion_amount}</td>
  </tr>
  ${adhesion.activites.map((activityName: string) => {
  const activity = allActivities.value.find((act: Activity) => act.name === activityName);
  if (activity) {
  return `       <tr>
                  <td style="padding: 8px; border: 1px solid #ddd;">Activité: ${ activity.name  }</td>
                  <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${ getPrice(activity, adhesion.ville)  }</td>
                </tr>`;
  } else {
  return `      <tr>
                  <td style="padding: 8px; border: 1px solid #ddd;">Activité: ${ activityName } (Non trouvée)</td>
                  <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">0.00</td>
                </tr>`;
  }
  }).join('')}
  <tr style="background-color: #f2f2f2;">
  <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">TOTAL PAYÉ</td>
  <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">${calculateTotalCost(adhesion)}</td>
  </tr>
  </tbody>
  </table>

  <div style="text-align: center; font-size: 8pt; color: #777;">
  <p>Foyer Rural de Fauverney - Association loi 1901</p>
  <p>Contact: contact@foyer-rural-fauverney.fr</p>
  <p>Merci pour votre adhésion !</p>
  </div>
  </div>
  `
;

  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = receiptContent;
  tempDiv.style.position = 'absolute';
  tempDiv.style.left = '-9999px';
  document.body.appendChild(tempDiv);

  try {
    const canvas = await html2canvas(tempDiv, { scale: 4 });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    });

    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();

    const imgWidth = canvas.width;
    const imgHeight = canvas.height;

    const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);

    const finalWidth = imgWidth * ratio;
    const finalHeight = imgHeight * ratio;

    const x = (pdfWidth - finalWidth) / 2;
    const y = (pdfHeight - finalHeight) / 2;

    pdf.addImage(imgData, 'PNG', x, y, finalWidth, finalHeight);

    pdf.save(

  `reçu_adhesion_${adhesion.code}.pdf`

);
  } catch (error) {
    console.error("Erreur lors de la génération du PDF:", error);
    alert("Impossible de générer le reçu PDF.");
  } finally {
    document.body.removeChild(tempDiv);
  }
};
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}

.validate-button {
  background-color: #28a745;
  margin-left: 10px;
}

.validate-button:hover {
  background-color: #218838;
}

.receipt-button {
  background-color: #007bff;
  margin-left: 10px;
}

.receipt-button:hover {
  background-color: #0056b3;
}


.button {
  display: inline-block;
  padding: 10px 15px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  margin-bottom: 0.5rem;
  margin-right: 0.5rem;
}

.button:hover {
  background-color: #0056b3;
}

.export-button {
  background-color: #28a745;
  margin-left: 0;
}

.export-button:hover {
  background-color: #218838;
}

.export-button {
  background-color: #28a745;
  margin-left: 0;
}

.export-button:hover {
  background-color: #218838;
}
</style>
