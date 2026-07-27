"""
Source unique de vérité pour la liste des villes du projet.
Tous les scripts (collect, backfill, transform, load_warehouse) importent
cette liste pour rester cohérents.
"""

CITIES = [
    {"city": "Antananarivo", "country": "Madagascar", "latitude": -18.8792, "longitude": 47.5079},
    {"city": "Toamasina",    "country": "Madagascar", "latitude": -18.1492, "longitude": 49.4023},  # Tamatave
    {"city": "Mahajanga",    "country": "Madagascar", "latitude": -15.7167, "longitude": 46.3167},  # Majunga
    {"city": "Fianarantsoa", "country": "Madagascar", "latitude": -21.4536, "longitude": 47.0854},
    {"city": "Toliara",      "country": "Madagascar", "latitude": -23.3516, "longitude": 43.6707},  # Tulear
]

# NB : "Majunga" et "Tamatave" et "Tulear" sont les noms coloniaux/usuels ;
# on garde les noms officiels malgaches (Mahajanga, Toamasina, Toliara) comme
# clé technique, et on documente les alias dans le README du stockage.
