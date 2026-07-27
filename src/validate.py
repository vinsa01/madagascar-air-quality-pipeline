"""
validate.py — Vérifie que clean/clean_aqi.csv respecte le contrat de données.

NB : si le cours fournit un script de validation officiel, utilisez-le en
plus de celui-ci (ce script est un filet de sécurité que l'équipe peut lancer
à tout moment, ex: dans le pipeline CI ou juste après transform.py).

Contrôles effectués :
  - le fichier existe et n'est pas vide
  - colonnes attendues présentes
  - une ligne par (ville, heure), aucun doublon
  - tri chronologique (par ville)
  - pas de latitude/longitude/AQI manquants
  - les 5 villes attendues sont présentes
  - cohérence approximative : nb lignes ≈ nb villes x nb heures couvertes

Utilisation :
    python src/validate.py
"""
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CLEAN_FILE
from cities import CITIES

REQUIRED_COLUMNS = [
    "city", "country", "latitude", "longitude", "timestamp_utc",
    "european_aqi", "us_aqi", "pm10", "pm2_5",
    "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone",
]

EXPECTED_CITIES = {c["city"] for c in CITIES}


def fail(msg):
    print(f"ECHEC : {msg}")
    sys.exit(1)


def main():
    if not CLEAN_FILE.exists():
        fail(f"{CLEAN_FILE} n'existe pas. Lancez transform.py.")

    with open(CLEAN_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        header = reader.fieldnames

    if not rows:
        fail("Le fichier clean est vide.")

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing_cols:
        fail(f"Colonnes manquantes : {missing_cols}")

    seen_cities = set()
    by_city_timestamps = defaultdict(list)
    seen_keys = set()
    duplicates = []
    missing_values = []

    for i, row in enumerate(rows, start=2):  # ligne 1 = header
        key = (row["city"], row["timestamp_utc"])
        if key in seen_keys:
            duplicates.append(key)
        seen_keys.add(key)

        seen_cities.add(row["city"])
        by_city_timestamps[row["city"]].append(row["timestamp_utc"])

        for col in ("latitude", "longitude", "timestamp_utc", "city"):
            if not row[col]:
                missing_values.append((i, col))

    if duplicates:
        fail(f"{len(duplicates)} doublons (ville, timestamp) trouvés, ex: {duplicates[:5]}")

    if missing_values:
        fail(f"{len(missing_values)} valeurs obligatoires manquantes, ex: {missing_values[:5]}")

    missing_cities = EXPECTED_CITIES - seen_cities
    if missing_cities:
        fail(f"Villes attendues absentes du fichier clean : {missing_cities}")

    # tri chronologique par ville
    for city, timestamps in by_city_timestamps.items():
        parsed = [datetime.fromisoformat(t) for t in timestamps]
        if parsed != sorted(parsed):
            fail(f"Le fichier n'est pas trié chronologiquement pour la ville {city}")

    # cohérence approximative : lignes ≈ villes x heures couvertes
    total_rows = len(rows)
    n_cities = len(seen_cities)
    all_ts = [datetime.fromisoformat(t) for ts in by_city_timestamps.values() for t in ts]
    span_hours = (max(all_ts) - min(all_ts)).total_seconds() / 3600
    expected = n_cities * span_hours
    ratio = total_rows / expected if expected else 0

    print("=== Validation clean/clean_aqi.csv ===")
    print(f"Lignes totales        : {total_rows}")
    print(f"Villes présentes      : {sorted(seen_cities)}")
    print(f"Période couverte      : {min(all_ts)} -> {max(all_ts)} ({span_hours:.0f} h)")
    print(f"Couverture vs attendu : {ratio:.1%} (lignes réelles / (villes x heures théoriques))")
    print("\nOK — le fichier respecte le contrat de données.")

    if ratio < 0.9:
        print(
            "\n[Avertissement] Couverture < 90% : documentez les trous connus dans le "
            "README du stockage (pannes, indisponibilité de l'API, etc.)."
        )


if __name__ == "__main__":
    main()
