# Rapport de projet — Pipeline AQI Madagascar

_Ce document est un template. Remplacez chaque section avant le rendu._

## Équipe

| Membre | Rôle principal | Contributions clés |
|---|---|---|
| ... | ex: collecte & API | ... |
| ... | ex: orchestration Airflow | ... |
| ... | ex: modélisation & warehouse | ... |
| ... | ex: validation & README | ... |
| ... | ex: déploiement & vidéo | ... |

## Méthode de travail

- Répartition des tâches : _(ex. par composant : collecte / transformation / warehouse / orchestration / documentation)_
- Fréquence des points d'équipe : ...
- Outil de suivi utilisé (Git issues, Trello, etc.) : ...
- Convention de commits : ...

## Choix techniques justifiés

_Reprendre et développer les points d'`ARCHITECTURE.md` avec le recul du groupe :
pourquoi Open-Meteo plutôt qu'une autre API, pourquoi Airflow plutôt qu'une
alternative plus légère, comment le déploiement continu a été résolu concrètement
(quelle machine, comment elle reste allumée), etc._

## Difficultés rencontrées et solutions

| Difficulté | Solution apportée |
|---|---|
| ex: limite de débit de l'API pendant le backfill | ex: pause de 0.5s entre appels, découpage mensuel |
| ex: Airflow qui s'arrête quand la machine se met en veille | ex: déploiement sur VM cloud toujours allumée |
| ... | ... |

## Preuves de fonctionnement

- Capture de l'historique des runs Airflow (≥ 5 jours différents, horaires sans intervention) : voir `docs/screenshots/`
- Lien vers la vidéo de démonstration (3 min max) : ...

## Limites connues et pistes d'amélioration

...
