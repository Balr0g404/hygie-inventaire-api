# Django DRF Boilerplate

Ce dépôt fournit un squelette Django + Django REST Framework pensé pour démarrer rapidement
un backend API moderne, sécurisé et documenté. Il inclut l'authentification JWT, des endpoints
techniques (health/ready/version), une base de configuration multi-environnements et une
documentation OpenAPI automatique.

## Fonctionnalités

- **Django 6 + DRF** pour une API REST robuste.
- **JWT (SimpleJWT)** avec refresh token et blacklist.
- **Endpoints techniques** : health, readiness, version.
- **Documentation API** : Swagger/Redoc via drf-spectacular.
- **Configuration par environnement** (base/local/production/ci).
- **Docker + docker-compose** pour la dev et la prod.

## Prérequis

- Python 3.12+
- Docker et Docker Compose (recommandé)
- MySQL (si vous lancez en dehors de Docker)

## Démarrage rapide (Docker)

```bash
cp .env.example .env
# éditez le fichier .env selon vos besoins

docker compose up --build
```

L'API sera disponible sur `http://localhost:8000`.

## Démarrage en local (sans Docker)

1. Créez et activez un environnement virtuel :
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Configurez vos variables d'environnement (voir section suivante).
4. Lancez les migrations :
   ```bash
   python manage.py migrate
   ```
5. Démarrez le serveur :
   ```bash
   python manage.py runserver
   ```

## Variables d'environnement principales

- `DJANGO_SETTINGS_MODULE` : `config.settings.local` (dev) ou `config.settings.production` (prod)
- `DJANGO_SECRET_KEY` : clé secrète Django
- `DJANGO_DEBUG` : `1` pour activer le debug
- `DJANGO_ALLOWED_HOSTS` : liste séparée par des virgules
- `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`
- `CORS_ALLOWED_ORIGINS` : liste séparée par des virgules

## Endpoints disponibles

### Authentification

- `POST /api/v1/auth/register/` : inscription
- `POST /api/v1/auth/jwt/create/` : obtenir un token JWT
- `POST /api/v1/auth/jwt/refresh/` : rafraîchir un token
- `POST /api/v1/auth/jwt/logout/` : invalider un refresh token
- `GET /api/v1/users/me/` : profil utilisateur

### Utilisateurs

- `GET /api/v1/users/` : liste des utilisateurs (admin)
- `GET /api/v1/users/{id}/` : détail d'un utilisateur (admin)
- `PATCH /api/v1/users/{id}/` : mise à jour (admin)
- `DELETE /api/v1/users/{id}/` : désactivation logique (admin)

### Core

- `GET /api/v1/health/`
- `GET /api/v1/ready/`
- `GET /api/v1/version/`

### Documentation

- `GET /api/schema/` (OpenAPI)
- `GET /api/docs/` (Swagger UI)
- `GET /api/redoc/` (Redoc)

## Tests

```bash
pytest
```

## Structure du projet

- `apps/accounts` : gestion des utilisateurs, auth JWT
- `apps/core` : endpoints techniques (health, ready, version)
- `config/settings` : configuration multi-environnements

## Déploiement

Le dépôt inclut `Dockerfile` et `docker-compose-prod.yml` pour une mise en production.
Assurez-vous d'utiliser `DJANGO_SETTINGS_MODULE=config.settings.production` et de fournir
les variables d'environnement requises.


Ce projet est maintenu par un développeur professionnel utilisant l'IA générative.