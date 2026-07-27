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
| `latitude` | float | degrés | Latitude WGS84 renvoyée par l'API (grille ~11 km, peut différer légèrement des coordonnées demandées) |
| `longitude` | float | degrés | Longitude WGS84 |
| `timestamp_utc` | string ISO 8601 | UTC | Horodatage de la mesure, ex `2026-07-25T14:00` |
| `european_aqi` | float | indice 0-100+ | AQI européen consolidé (max de tous les sous-indices) |
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

_À compléter par le groupe après le backfill initial, ex :_
`2025-07-25` → `2026-07-25` (12 mois), mise à jour continue toutes les heures depuis le `2026-07-XX`.

## Trous connus

_À compléter par le groupe_ — ex : indisponibilité ponctuelle de l'API, panne du
scheduler Airflow entre telle et telle date, etc. Documenter ici tout écart
entre `nombre de lignes réel` et `nombre de villes × nombre d'heures théoriques`
(voir la sortie de `src/validate.py`).

## Infos de connexion à la base

- Moteur : PostgreSQL (hébergement : Supabase ou Neon — _à préciser_)
- Hôte : `<à compléter, ex: xxxxx.supabase.co>`
- Port : `5432`
- Base : `postgres`
- Utilisateur en lecture pour IA1 : `<à créer si besoin d'un accès restreint>`
- **Le mot de passe n'est jamais écrit ici** — il est transmis séparément
  (canal privé au correcteur / au cours IA1), jamais dans le repo Git.
