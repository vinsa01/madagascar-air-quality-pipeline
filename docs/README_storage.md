# \# README du stockage

# 

# \## Villes choisies

# 

# | Ville (clé technique) | Alias courant | Pays | Latitude | Longitude |

# |---|---|---|---|---|

# | Antananarivo | — | Madagascar | -18.8792 | 47.5079 |

# | Toamasina | Tamatave | Madagascar | -18.1492 | 49.4023 |

# | Mahajanga | Majunga | Madagascar | -15.7167 | 46.3167 |

# | Fianarantsoa | — | Madagascar | -21.4536 | 47.0854 |

# | Toliara | Tulear | Madagascar | -23.3516 | 43.6707 |

# 

# \## Colonnes de `data/clean/clean\_aqi.csv` et unités

# 

# | Colonne | Type | Unité / format | Description |

# |---|---|---|---|

# | `city` | string | — | Nom de la ville (clé technique ci-dessus) |

# | `country` | string | — | Toujours "Madagascar" |

# | `latitude` | float | degrés | Latitude WGS84 renvoyée par l'API |

# | `longitude` | float | degrés | Longitude WGS84 |

# | `timestamp\_utc` | string ISO 8601 | UTC | Horodatage de la mesure, ex `2026-07-25T14:00` |

# | `european\_aqi` | float | indice 0-100+ | AQI européen consolidé |

# | `us\_aqi` | float | indice 0-500 | AQI américain consolidé |

# | `pm10` | float | µg/m³ | Particules < 10 µm |

# | `pm2\_5` | float | µg/m³ | Particules < 2.5 µm |

# | `carbon\_monoxide` | float | µg/m³ | Monoxyde de carbone |

# | `nitrogen\_dioxide` | float | µg/m³ | Dioxyde d'azote |

# | `sulphur\_dioxide` | float | µg/m³ | Dioxyde de soufre |

# | `ozone` | float | µg/m³ | Ozone |

# 

# Une ligne = une ville x une heure. Fichier trié par ville puis par `timestamp\_utc`

# croissant, sans doublons (clé unique = `city` + `timestamp\_utc`).

# 

# \## Schéma du warehouse

# 

# Schéma en étoile — voir `src/db\_schema.sql` pour le DDL complet.

# 

# \- `dim\_city(city\_id, city\_name, country, latitude, longitude)`

# \- `dim\_time(time\_id, full\_timestamp, date, year, month, day, hour, day\_of\_week, day\_of\_week\_num, is\_weekend)`

# \- `fact\_aqi(fact\_id, city\_id, time\_id, european\_aqi, us\_aqi, pm10, pm2\_5, carbon\_monoxide, nitrogen\_dioxide, sulphur\_dioxide, ozone)`

# 

# Grain de `fact\_aqi` : une ligne par (ville, heure).

# 

# \## Période couverte

# 

# \*\*2025-07-27 → 2026-07-27 (12 mois complets)\*\*, backfill effectué le 27/07/2026,

# puis mise à jour continue toutes les heures via Airflow depuis le \[à compléter

# une fois Airflow lancé].

# 

# Couverture validée : \*\*100%\*\* (43 830 lignes de faits pour 5 villes × 8766 heures

# théoriques). Voir `src/validate.py` pour la méthode de calcul.

# 

# \## Trous connus

# 

# Aucun trou dans les données finales : quelques appels à l'API ont rencontré des

# timeouts ponctuels pendant le backfill (connexion réseau instable côté client),

# mais le mécanisme de réessai automatique de `backfill.py` (3 tentatives, délai

# progressif) les a tous résolus. Résultat final : 60/60 appels réussis, 0 échec,

# couverture 100%.

# 

# \## Infos de connexion à la base

# 

# \- Moteur : PostgreSQL, hébergé sur \*\*Supabase\*\*

# \- Connexion : via le \*\*Connection Pooler\*\* de Supabase (mode session), requis

# &#x20; car la connexion directe (IPv6) n'est pas supportée par tous les réseaux

# \- Hôte : `aws-0-eu-north-1.pooler.supabase.com`

# \- Port : `5432`

# \- Base : `postgres`

# \- Utilisateur : `postgres.<project\_ref>` (voir `.env`, jamais commité)

# \- \*\*Le mot de passe n'est jamais écrit ici\*\* — il est transmis séparément

# &#x20; (canal privé au correcteur / au cours IA1), jamais dans le repo Git.

