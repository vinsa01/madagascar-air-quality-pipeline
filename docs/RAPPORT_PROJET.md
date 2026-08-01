# \# Rapport de projet — Pipeline AQI Madagascar

# 

# \## Équipe

# 

# | Membre | Rôle principal | Contributions clés |

# |---|---|---|

# | Vinsa (vinsa01) | Infrastructure \& DevOps | Setup Supabase, déploiement Airflow/Docker sur VM Ubuntu, debug intégral du pipeline (connexions, DNS, résilience), gestion Git |

# | Anjara | Corrections techniques | Correctif DNS (résolution intermittente), amélioration de la résilience des retries Airflow |

# 

# \## Méthode de travail

# 

# Le groupe s'est organisé autour d'un dépôt Git central (GitHub), avec un membre pilotant l'infrastructure (déploiement Airflow, base de données) pendant que le reste du groupe se répartissait la documentation, la relecture et la préparation des livrables finaux (rapport, vidéo).

# 

# Le suivi s'est fait principalement en direct (messages instantanés) pour réagir rapidement aux blocages techniques rencontrés pendant le déploiement, avec des points de synchronisation fréquents les derniers jours avant le rendu pour répartir les tâches restantes.

# 

# Convention de commits : messages descriptifs en français, un commit par correction ou fonctionnalité, pour garder un historique lisible du déroulement réel du projet.

# 

# \## Choix techniques justifiés

# 

# \*\*Source de données — Open-Meteo Air Quality API\*\* : choisie car elle ne nécessite aucune clé API et permet un backfill historique complet (données disponibles depuis août 2022 pour la région Madagascar), contrairement à la plupart des APIs concurrentes limitées à quelques jours d'historique en accès gratuit. Ce choix s'est avéré déterminant pour respecter la contrainte de backfill 12 mois du sujet.

# 

# \*\*Orchestrateur — Apache Airflow (Docker Compose)\*\* : choisi pour sa robustesse et son interface native de suivi des exécutions (essentielle pour la preuve d'exécution demandée). Ce choix s'est avéré plus coûteux en temps de déploiement que prévu (voir difficultés ci-dessous), notamment sur une connexion internet limitée, mais offre en contrepartie une visibilité complète et un historique fiable des runs.

# 

# \*\*Hébergement de l'orchestrateur — VM Ubuntu locale (VMware) plutôt qu'un serveur cloud\*\* : par contrainte de temps et d'accès à une carte bancaire pour un VPS payant, le groupe a choisi de faire tourner Airflow sur une machine virtuelle locale laissée allumée en continu. Ce choix impose une dépendance à la disponibilité de cette machine (voir difficultés), documentée et assumée dans ce rapport.

# 

# \*\*Base de données — PostgreSQL managé (Supabase, offre gratuite)\*\* : choisi pour son accessibilité externe (le correcteur et le cours IA1 peuvent s'y connecter sans dépendre de l'infrastructure du groupe), répondant directement à l'exigence du sujet qu'un livrable ne soit jamais "invérifiable". La connexion directe (IPv6) s'étant révélée incompatible avec le réseau utilisé, le groupe est passé par le Connection Pooler de Supabase (IPv4), une solution plus universellement compatible.

# 

# \*\*Modélisation — schéma en étoile\*\* : choisi plutôt qu'un flocon car les 5 villes du projet appartiennent toutes au même pays (Madagascar) et la dimension temps ne nécessite aucune hiérarchie complexe à normaliser. Un flocon aurait ajouté des jointures sans bénéfice réel pour ce volume et cette structure de données.

# 

# \## Difficultés rencontrées et comment nous les avons résolues

# 

# | Difficulté | Cause | Solution apportée |

# |---|---|---|

# | `psycopg2-binary` ne s'installait pas sous Windows (Python 3.13) | Absence de wheel précompilé pour cette version récente de Python sous Windows | Migration vers `psycopg` v3, qui dispose de wheels précompilés pour Python 3.13 |

# | Connexion directe à Supabase impossible depuis certains réseaux | La connexion directe nécessite IPv6, non supporté par le réseau utilisé | Utilisation du Connection Pooler de Supabase (IPv4) à la place de la connexion directe |

# | Imports Python locaux (`config.py`, `cities.py`) introuvables sous Windows | `PYTHONSAFEPATH` (Python 3.13+) empêche l'ajout automatique du dossier du script à `sys.path` | Ajout explicite du dossier du script à `sys.path` dans chaque fichier concerné |

# | Airflow (webserver) ne trouvait pas `psycopg2` malgré son installation | Chaque conteneur Docker installe ses dépendances indépendamment ; seul `airflow-init` les avait installées | Volume Docker partagé pour les paquets Python (`/home/airflow/.local`) entre tous les conteneurs, avec attente explicite (`condition: service\_completed\_successfully`) que l'initialisation soit terminée avant le démarrage des autres services |

# | Téléchargement des images Docker très long et sujet à coupures | Connexion internet limitée (\~20-30 KB/s) | Passage à des images Docker allégées ("slim" pour Airflow, "alpine" pour Postgres) et relance automatique en boucle jusqu'à succès (les couches déjà téléchargées étant mises en cache) |

# | Résolution DNS intermittente dans les conteneurs (`Temporary failure in name resolution`) | Instabilité réseau ponctuelle de l'environnement d'hébergement | Configuration de serveurs DNS explicites et fiables (8.8.8.8, 1.1.1.1) dans `docker-compose.yaml`, et augmentation du nombre de tentatives (retries) et du délai entre elles dans le DAG Airflow |

# | Redémarrages système imprévus (mise à jour Windows automatique) interrompant le pipeline | Mise à jour Windows lancée sans confirmation explicite | Ajout de `restart: always` sur l'ensemble des services Docker (y compris la base de métadonnées Airflow, initialement oubliée), permettant une reprise automatique sans intervention manuelle ; suspension des mises à jour Windows pour la durée du projet |

# | Erreur de certificat SSL lors de la connexion Power BI à Supabase | Le connecteur PostgreSQL natif de Power BI ne propose pas d'option pour assouplir la validation de certificat | Non résolu au moment de la rédaction ; à investiguer via un connecteur ODBC si nécessaire pour le projet individuel |

# 

# \## Preuves de fonctionnement

# 

# \- Historique des runs Airflow (`http://localhost:8080/dags/air\_quality\_pipeline/grid`) : captures d'écran disponibles dans `docs/screenshots/`, couvrant plusieurs jours différents (27, 28, 29, 30, 31 juillet 2026), incluant des runs exécutés sans surveillance (nuit, tôt le matin).

# \- Requêtes SQL de vérification exécutées directement sur le warehouse Supabase (couverture des données, répartition par mois) — voir section suivante.

# \- Lien vers la vidéo de démonstration : \[à compléter]

# 

# \## Limites connues et pistes d'amélioration

# 

# \- L'orchestrateur tourne sur une machine locale plutôt qu'un serveur cloud dédié ; une migration vers un VPS ou une offre cloud gratuite (Oracle Cloud, par exemple) renforcerait la continuité du service après la fin du projet.

# \- Quelques heures de données ponctuellement manquantes suite aux incidents réseau documentés ci-dessus (voir aussi `docs/README\_storage.md`, section "trous connus").

# \- La connexion Power BI à Supabase nécessite une configuration supplémentaire (connecteur ODBC) non finalisée au moment du rendu.

