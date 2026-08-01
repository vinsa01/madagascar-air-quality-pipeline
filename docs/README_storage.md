# README du stockage

## Villes choisies

| Ville (clé technique) | Alias courant | Pays | Latitude | Longitude |
|---|---|---|---|---|
| Antananarivo | — | Madagascar | -18.8792 | 47.5079 |
| Toamasina | Tamatave | Madagascar | -18.1492 | 49.4023 |
| Mahajanga | Majunga | Madagascar | -15.7167 | 46.3167 |
| Fianarantsoa | — | Madagascar | -21.4536 | 47.0854 |
| Toliara | Tulear | Madagascar | -23.3516 | 43.6707 |

## Colonnes de `data/clean/clean_aqi.csv` et unités

| Colonne | Type | Unité / format | Description |
|---|---|---|---|
| `city` | string | — | Nom de la ville (clé technique ci-dessus) |
| `country` | string | — | Toujours "Madagascar" |
| `latitude` | float | degrés | Latitude WGS84 renvoyée par l'API |
| `longitude` | float | degrés | Longitude WGS84 |
| `timestamp_utc` | string ISO 8601 | UTC | Horodatage de la mesure, ex `2026-07-25T14:00` |
| `european_aqi` | float | indice 0-100+ | AQI européen consolidé |
| `us_aqi` | float | indice 0-500 | AQI américain consolidé |
| `pm10` | float | µg/m³ | Particules < 10 µm |
| `pm2_5` | float | µg/m³ | Particules < 2.5 µm |
| `carbon_monoxide` | float | µg/m³ | Monoxyde de carbone |
| `nitrogen_dioxide` | float | µg/m³ | Dioxyde d'azote |
| `sulphur_dioxide` | float | µg/m³ | Dioxyde de soufre |
| `ozone` | float | µg/m³ | Ozone |

Une ligne = une ville x une heure. Fichier trié par ville puis par `timestamp_utc`
croissant, sans doublons (clé unique = `city` + `timestamp_utc`).

## Schéma du warehouse

Schéma en étoile — voir `src/db_schema.sql` pour le DDL complet.

- `dim_city(city_id, city_name, country, latitude, longitude)`
- `dim_time(time_id, full_timestamp, date, year, month, day, hour, day_of_week, day_of_week_num, is_weekend)`
- `fact_aqi(fact_id, city_id, time_id, european_aqi, us_aqi, pm10, pm2_5, carbon_monoxide, nitrogen_dioxide, sulphur_dioxide, ozone)`

Grain de `fact_aqi` : une ligne par (ville, heure).

## Période couverte

**2025-07-27 → 2026-07-27 (12 mois complets)**, backfill effectué le 27/07/2026,
puis mise à jour continue toutes les heures via Airflow depuis le [à compléter
une fois Airflow lancé].

Couverture validée : **100%** (43 830 lignes de faits pour 5 villes × 8766 heures
théoriques). Voir `src/validate.py` pour la méthode de calcul.

## Trous connus

Aucun trou dans les données finales : quelques appels à l'API ont rencontré des
timeouts ponctuels pendant le backfill (connexion réseau instable côté client),
mais le mécanisme de réessai automatique de `backfill.py` (3 tentatives, délai
progressif) les a tous résolus. Résultat final : 60/60 appels réussis, 0 échec,
couverture 100%.
Trou ponctuel le 29/07 vers 04h UTC : échec de résolution DNS transitoire dans le conteneur Docker (3 tentatives, ~15 min), 1 heure de données manquante pour toutes les villes. Corrigé en configurant des serveurs DNS explicites (8.8.8.8, 1.1.1.1) et en augmentant le nombre de tentatives du DAG.

## Infos de connexion à la base

- Moteur : PostgreSQL, hébergé sur **Supabase**
- Connexion : via le **Connection Pooler** de Supabase (mode session), requis
  car la connexion directe (IPv6) n'est pas supportée par tous les réseaux
- Hôte : `aws-0-eu-north-1.pooler.supabase.com`
- Port : `5432`
- Base : `postgres`
- Utilisateur : `postgres.<project_ref>` (voir `.env`, jamais commité)
- **Le mot de passe n'est jamais écrit ici** — il est transmis séparément
  (canal privé au correcteur / au cours IA1), jamais dans le repo Git.
