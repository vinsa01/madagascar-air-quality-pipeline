# ARCHITECTURE.md

## Vue d'ensemble

```
Open-Meteo Air Quality API (5 villes de Madagascar)
        │  collecte horaire (collect.py) + backfill (backfill.py)
        ▼
Airflow (Docker, déployé sur [VM à préciser par le groupe])
        │  DAG air_quality_pipeline : collect >> transform >> load_warehouse
        │  DAG air_quality_backfill : backfill >> transform >> load_warehouse
        ▼
STOCKAGE (dans le repo Git)
  data/raw/<ville>/<ville>_<timestamp>.json   — jamais modifié
  data/clean/clean_aqi.csv                    — reconstruit à chaque run
        ▼
DATA WAREHOUSE — PostgreSQL (Supabase/Neon), schéma en étoile
  dim_city, dim_time, fact_aqi
```

## Choix techniques et justifications

| Composant | Choix | Justification |
|---|---|---|
| **Source de données** | Open-Meteo Air Quality API | Gratuite, sans clé API, et surtout : couvre l'historique horaire pour Madagascar depuis août 2022 (domaine CAMS global), ce qui rend le backfill de 12 mois réalisable sans budget — contrairement à la plupart des APIs concurrentes limitées à quelques jours d'historique en accès gratuit. |
| **Orchestrateur** | Apache Airflow (Docker Compose) | Choisi par le groupe pour sa robustesse et sa lisibilité (UI native pour visualiser l'historique des runs = preuve d'exécution directe), au prix de devoir maintenir un conteneur actif en continu. |
| **Hébergement Airflow** | VM continue (à préciser : ex. Oracle Cloud free tier / VPS étudiant / machine du groupe) | Airflow n'est pas serverless : il faut un scheduler qui tourne 24h/24. C'est la contrepartie du choix "Airflow" vs une alternative serverless comme GitHub Actions. |
| **Stockage raw/clean** | Fichiers dans le repo Git (JSON bruts + CSV unique) | Simplicité, traçabilité via Git, conforme à la contrainte "raw intouchable / clean reconstruit". |
| **Data warehouse** | PostgreSQL managé (Supabase ou Neon, offre gratuite) | Accessible depuis n'importe où (Airflow, IA1, correcteur) sans que le groupe héberge sa propre base — répond à l'exigence "livrable vérifiable, jamais de base qui ne répond pas". |
| **Modélisation** | Schéma en étoile (1 fait + 2 dimensions) | Le grain (ville x heure) est simple et stable dans le temps ; un flocon n'apporterait pas de valeur ici (pas de hiérarchies à normaliser sur ville ou temps). |

## Schéma dimensionnel

- **fact_aqi** : mesures (european_aqi, us_aqi, pm10, pm2_5, carbon_monoxide, nitrogen_dioxide, sulphur_dioxide, ozone) + clés étrangères `city_id`, `time_id`. Aucune colonne descriptive.
- **dim_city** : `city_name`, `country`, `latitude`, `longitude`. Aucune mesure.
- **dim_time** : `date`, `hour`, `day_of_week`, `is_weekend`, etc. Aucune mesure.

Grain de la table de faits : **une ligne par (ville, heure)**.

## Idempotence et rejouabilité

- `backfill.py` : ignore les tranches déjà téléchargées (basé sur les fichiers présents dans `raw/`), donc rejouable sans dupliquer les appels API.
- `transform.py` : reconstruit `clean/` en entier à chaque exécution à partir de `raw/`.
- `load_warehouse.py` : upsert (`ON CONFLICT`) sur les dimensions et sur `(city_id, time_id)` pour les faits — relancer le chargement ne duplique jamais rien.

## Ce que le groupe doit encore compléter

- [ ] Héberger le conteneur Airflow sur une machine qui reste allumée jusqu'au-delà du rendu (le cours IA1 doit continuer à recevoir des données).
- [ ] Créer le projet Supabase/Neon et renseigner `.env` (jamais commité).
- [ ] Lancer `backfill.py --months 12` une première fois pour peupler l'historique.
- [ ] Vérifier dans l'UI Airflow que plusieurs runs réussis apparaissent sur ≥ 5 jours différents, à des heures sans intervention humaine (capture à fournir).
