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

## Déploiement avec Docker

Pour compiler le projet, générer une image Docker et lancer le conteneur, suivez ces étapes :

1.  **Construire l'image Docker :**
    Assurez-vous d'être à la racine du projet (là où se trouve le `Dockerfile`).
    ```bash
    docker build -t foyer-rural-app .
    ```
    Cette commande va construire l'image Docker nommée `foyer-rural-app`.

2.  **Lancer le conteneur Docker :**
    ```bash
    docker run -p 8000:8000 -e BACKEND_URL=http://your-backend-fqdn:8000 foyer-rural-app
    ```
    Remplacez `http://your-backend-fqdn:8000` par l'adresse réelle de votre backend. Si vous ne spécifiez pas `BACKEND_URL`, la valeur par défaut `http://localhost:8000` sera utilisée.

    Cette commande lance un conteneur à partir de l'image `foyer-rural-app` et mappe le port 8000 du conteneur au port 8000 de votre machine hôte.

    L'application sera accessible via votre navigateur à l'adresse `http://localhost:8000`.

    *Note : Le fichier `foyer_rural.db` (base de données SQLite) sera créé à l'intérieur du conteneur. Si vous souhaitez persister les données, vous devrez utiliser un volume Docker.*

3.  **Persister les données de la base de données (avec un volume Docker) :**
    Pour éviter de perdre vos données à chaque fois que le conteneur est supprimé, vous pouvez monter un volume Docker. Cela permet de stocker le fichier `foyer_rural.db` sur votre machine hôte.

    ```bash
    docker run -p 8000:8000 -v foyer-rural-db:/app/backend foyer-rural-app
    ```
    Dans cette commande :
    - `-v foyer-rural-db:/app/backend` : Crée un volume nommé `foyer-rural-db` et le monte dans le répertoire `/app/backend` à l'intérieur du conteneur. C'est dans ce répertoire que le fichier `foyer_rural.db` est créé par l'application FastAPI.

    Vous pouvez également monter un répertoire local de votre machine hôte :
    ```bash
    docker run -p 8000:8000 -v $(pwd)/data:/app/backend foyer-rural-app
    ```
    Dans cet exemple, le répertoire `data` (qui sera créé à la racine de votre projet sur votre machine hôte) sera monté dans `/app/backend` à l'intérieur du conteneur. Le fichier `foyer_rural.db` sera alors stocké dans le répertoire `data` de votre projet sur votre machine.
