# Guide d'installation - Campus Parler

Ce document détaille la procédure d'installation de l'application Campus Parler.

## Prérequis

- Python 3.8+ (recommandé 3.9+)
- pip (gestionnaire de paquets Python)
- Git

## 1. Récupération du code source

Clonez le dépôt Git dans votre répertoire de travail (HTTPS, SSH ne marche pas !) :

```bash
git clone https://gitlabsu.sorbonne-universite.fr/lu2in013/fev2025/gr1/badas.git
cd badas
```

## 2. Installation de l'environnement virtuel

L'environnement virtuel permet d'isoler les dépendances du projet des autres projets Python sur votre système et ne pas encombrer ce dernier.

### 2.1 Installation de virtualenv (si nécessaire)

```bash
pip install virtualenv
# ou selon votre configuration
pip3 install virtualenv
```

### 2.2 Création de l'environnement virtuel

```bash
python -m venv venv
# ou selon votre configuration python
python3 -m venv venv
```

### 2.3 Activation de l'environnement virtuel

**Sous Linux/macOS** :
```bash
source venv/bin/activate
```

**Sous Windows** : (à verifier)
```bash
venv\Scripts\activate
```

Une fois activé, votre invite de commande devrait changer pour indiquer le nom de l'environnement virtuel, par exemple : `(venv) $`.

## 3. Installation des dépendances

Une fois dans l'environnement virtuel activé, installez les dépendances du projet :

```bash
pip install -r requirements.txt
```

## 4. Configuration de la base de données

### 4.1 Configuration initiale

Le projet utilise SQLite.

### 4.2 Création de la base de données

Exécutez les migrations pour créer le schéma de base de données :

```bash
python manage.py migrate
```

### 4.3 Création d'un superutilisateur (facultatif)

Pour accéder à l'interface d'administration :

```bash
python manage.py createsuperuser
```

Suivez les instructions pour créer un compte administrateur.

## 5. Lancement du serveur de développement

Une fois l'installation terminée, vous pouvez lancer le serveur de développement :

```bash
python manage.py runserver
```

Le site sera accessible à l'adresse http://127.0.0.1:8000/

L'interface d'administration est disponible à http://127.0.0.1:8000/admin/ (si vous avez créé un superutilisateur).

## 6. Lancement des tests

Vous pouvez lancer les tests avec la commande suivante :

```bash
python manage.py test app.tests
```

## 7. Résolution des problèmes courants

### 7.1 Problèmes de dépendances

Si vous rencontrez des erreurs lors de l'installation des dépendances, essayez de mettre à jour pip :

```bash
pip install --upgrade pip
```

### 7.2 Problèmes de migrations

Si vous rencontrez des erreurs de migration, vous pouvez essayer de réinitialiser la base de données :

```bash
# Supprime le fichier db.sqlite3
rm db.sqlite3
# Réappliquer les migrations
python manage.py migrate
```

## 8. Notes

- N'oubliez pas d'ajouter le nom de votre environnement virtuel (ex: "venv") dans votre fichier `.gitignore` pour éviter de l'envoyer au dépôt Git.
- Pour quitter l'environnement virtuel, utilisez la commande `deactivate`.
- Après avoir modifié les modèles, n'oubliez pas d'exécuter `python manage.py makemigrations` suivi de `python manage.py migrate`.
