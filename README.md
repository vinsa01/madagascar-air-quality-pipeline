# Pipeline AQI — 5 villes de Madagascar

Pipeline de collecte automatique de la qualité de l'air (Antananarivo, Toamasina,
Mahajanga, Fianarantsoa, Toliara) vers un data warehouse dimensionnel.

Voir [`ARCHITECTURE.md`](./ARCHITECTURE.md) pour la stack et les choix techniques,
et [`docs/README_storage.md`](./docs/README_storage.md) pour le contrat de données.

## Démarrage rapide (développement local, sans Airflow)

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer les secrets
cp .env.example .env
# éditez .env avec vos identifiants Supabase/Neon

# 3. Backfill historique (une seule fois, rejouable si interrompu)
cd src
python backfill.py --months 12

# 4. Reconstruire le fichier clean
python transform.py

# 5. Valider le contrat de données
python validate.py

# 6. Charger le data warehouse
python load_warehouse.py

# 7. Test d'une collecte "live" (celle qu'Airflow exécutera toutes les heures)
python collect.py
```

## Démarrage avec Airflow (production)

```bash
cp .env.example .env   # puis complétez-le
docker compose up airflow-init
docker compose up -d
# UI sur http://localhost:8080 (airflow / airflow)
# Activez les DAGs "air_quality_pipeline" (horaire) et déclenchez une fois
# "air_quality_backfill" manuellement.
```

## Structure du repo

```
src/                    scripts Python (collecte, transformation, chargement, validation)
airflow/dags/           DAGs Airflow
data/raw/               données brutes, jamais modifiées (1 fichier par ville par appel)
data/clean/             clean_aqi.csv, reconstruit à chaque run
docs/                   README du stockage, rapport de projet
ARCHITECTURE.md         stack + justifications
docker-compose.yaml     déploiement Airflow
```
