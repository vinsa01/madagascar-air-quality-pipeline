"""
Source unique de vérité pour la liste des villes du projet.
Tous les scripts (collect, backfill, transform, load) importent
cette liste pour rester cohérents.
"""

CITIES = [
    {"city": "Antananarivo", "country": "Madagascar", "latitude": -18.8792, "longitude": 47.5079},
    {"city": "Toamasina",    "country": "Madagascar", "latitude": -18.1492, "longitude": 49.4023},
    {"city": "Mahajanga",    "country": "Madagascar", "latitude": -15.7167, "longitude": 46.3167},
    {"city": "Fianarantsoa", "country": "Madagascar", "latitude": -21.4536, "longitude": 47.0854},
    {"city": "Toliara",      "country": "Madagascar", "latitude": -23.3516, "longitude": 43.6707},
]
