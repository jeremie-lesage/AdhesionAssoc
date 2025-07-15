# Projet de Formulaire d'Inscription

Ce projet est une application web permettant de gérer les demandes d'adhésion pour une association. Elle est composée d'un backend en Python avec FastAPI et d'un frontend en Vue.js, utilisant PostgreSQL comme base de données.

## Structure du Projet

- `/backend`: Contient l'application FastAPI.
- `/frontend`: Contient l'application Vue.js.
- `/docker`: Contient la configuration Docker Compose et Nginx.

## Démarrage Rapide

### Backend

1.  **Se placer dans le répertoire du backend :**
    ```bash
    cd backend
    ```

2.  **Installer les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Lancer le serveur de développement :**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
    Le backend sera alors accessible à l'adresse `http://localhost:8000`.

### Frontend

1.  **Se placer dans le répertoire du frontend :**
    ```bash
    cd frontend
    ```

2.  **Installer les dépendances :**
    ```bash
    npm install
    ```

3.  **Lancer le serveur de développement :**
    ```bash
    npm run dev
    ```
    Le frontend sera alors accessible à l'adresse `http://localhost:5173`.

## Utilisation

Une fois les deux serveurs (backend et frontend) lancés, vous pouvez ouvrir votre navigateur et vous rendre sur `http://localhost:5173` pour accéder au formulaire d'inscription.

- Pour remplir un nouveau formulaire, cliquez sur "Nouveau Formulaire".
- Pour charger un formulaire existant, cliquez sur "Charger un Formulaire" et saisissez le code qui vous a été fourni lors de la première soumission.

## Déploiement avec Docker Compose

Pour lancer l'ensemble de l'application (frontend, backend, base de données PostgreSQL et reverse proxy) avec Docker, vous pouvez utiliser Docker Compose.

1.  **Assurez-vous d'avoir Docker et Docker Compose installés sur votre machine.**

2.  **Créer le fichier `.env` :**
    Créez un fichier nommé `.env` dans le répertoire `docker/` avec le contenu suivant (vous pouvez modifier les valeurs) :
    ```
    POSTGRES_DB=foyer_db
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    PGADMIN_DEFAULT_EMAIL=admin@example.com
    PGADMIN_DEFAULT_PASSWORD=admin
    ```

3.  **Arrêter et supprimer les conteneurs et volumes existants (recommandé pour une nouvelle installation ou migration) :**
    Placez-vous à la racine du projet et exécutez la commande suivante :
    ```bash
    docker compose -f docker/compose.yml down -v
    ```
    Ceci supprimera les anciens volumes, y compris l'ancienne base de données SQLite si elle existait.

4.  **Lancer les services :**
    Placez-vous à la racine du projet et exécutez la commande suivante :
    ```bash
    docker compose -f docker/compose.yml up -d --build
    ```
    Cette commande va :
    - Construire les images pour le frontend et le backend.
    - Démarrer les conteneurs pour le frontend, le backend, la base de données PostgreSQL, PGAdmin et le proxy Nginx en arrière-plan (`-d`).

5.  **Accéder à l'application :**
    Une fois les conteneurs démarrés, l'application est accessible via votre navigateur à l'adresse `http://localhost:8000`.

    - Le reverse proxy Nginx écoute sur le port 8000 et redirige le trafic :
        - Les requêtes vers `/api/...` sont transmises au backend.
        - Toutes les autres requêtes sont servies par le frontend.

6.  **Accéder à PGAdmin :**
    PGAdmin est accessible à l'adresse `http://localhost:8080` avec les identifiants configurés dans le fichier `.env`.

7.  **Arrêter les services :**
    Pour arrêter tous les conteneurs, utilisez la commande :
    ```bash
    docker compose -f docker/compose.yml down
    ```