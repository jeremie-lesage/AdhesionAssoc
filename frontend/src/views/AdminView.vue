<template>
  <div class="admin-view">
    <h1>Espace Administration</h1>
    <p>Bienvenue dans l'espace d'administration. Choisissez une section à gérer.</p>
    <nav class="admin-nav">
      <ul>
        <li>
          <RouterLink to="/admin/adhesions" class="nav-link">
            <span class="icon">📄</span>
            <span>Gérer les Demandes d'Adhésion</span>
          </RouterLink>
        </li>
        <li>
          <RouterLink to="/admin/contacts" class="nav-link">
            <span class="icon">📧</span>
            <span>Gérer les Demandes par Contact</span>
          </RouterLink>
        </li>
        <li>
          <RouterLink to="/admin/activities" class="nav-link">
            <span class="icon">🤸</span>
            <span>Gérer les Activités</span>
          </RouterLink>
        </li>
        <li>
          <RouterLink to="/admin/adherents-by-activity" class="nav-link">
            <span class="icon">👥</span>
            <span>Voir les Adhérents par Activité</span>
          </RouterLink>
        </li>
        <li>
          <RouterLink to="/admin/accounts" class="nav-link">
            <span class="icon">🔑</span>
            <span>Gérer les Comptes Administrateur</span>
          </RouterLink>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router';
</script>

<style scoped>
.admin-view {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 1.5rem;
}

p {
  text-align: center;
  color: #666;
  margin-bottom: 2rem;
}

.admin-nav ul {
  list-style: none;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 1rem;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  text-decoration: none;
  color: #333;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.nav-link:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--color-primary);
}

.nav-link .icon {
  font-size: 1.5rem;
  margin-right: 1rem;
}

.nav-link span {
  font-weight: 500;
}
</style>
