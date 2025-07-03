# Projet de Formulaire d'Inscription

Ce projet est une application web permettant de gérer les demandes d'adhésion pour une association. Elle est composée d'un backend en Python avec FastAPI et d'un frontend en Vue.js.

## Structure du Projet

- `/backend`: Contient l'application FastAPI.
- `/frontend`: Contient l'application Vue.js.

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
