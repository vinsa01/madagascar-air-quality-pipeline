"""
transform.py — Reconstruit clean/clean_aqi.csv EN ENTIER à partir de data/raw/.

Principe : raw/ est la source de vérité. Ce script ne fait que relire tous les
fichiers bruts, aplatir chaque (ville, heure) en une ligne, dédupliquer sur
(ville, timestamp) en gardant la mesure la plus récemment collectée en cas de
recouvrement entre collect.py (live) et backfill.py (historique), trier
chronologiquement, et réécrire le CSV depuis zéro.

C'est pour cela que clean/ peut être supprimé sans perte : il est toujours
reconstructible avec `python src/transform.py`.

Utilisation :
    python src/transform.py
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import RAW_DIR, CLEAN_DIR, CLEAN_FILE

FIELDNAMES = [
    "city", "country", "latitude", "longitude", "timestamp_utc",
    "european_aqi", "us_aqi", "pm10", "pm2_5",
    "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone",
]


def parse_raw_file(path: Path):
    """Transforme un fichier JSON brut (1 ville, 1 appel) en liste de lignes plates."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    meta = raw["_meta"]
    api = raw["api_response"]
    hourly = api.get("hourly", {})
    times = hourly.get("time", [])

    # position du fichier dans le "temps de collecte" -> sert au dédoublonnage
    collected_at = meta["collected_at_utc"]

    rows = []
    for i, ts in enumerate(times):
        row = {
            "city": meta["city"],
            "country": meta["country"],
            "latitude": api.get("latitude", meta["requested_latitude"]),
            "longitude": api.get("longitude", meta["requested_longitude"]),
            "timestamp_utc": ts,
            "european_aqi": hourly.get("european_aqi", [None] * len(times))[i],
            "us_aqi": hourly.get("us_aqi", [None] * len(times))[i],
            "pm10": hourly.get("pm10", [None] * len(times))[i],
            "pm2_5": hourly.get("pm2_5", [None] * len(times))[i],
            "carbon_monoxide": hourly.get("carbon_monoxide", [None] * len(times))[i],
            "nitrogen_dioxide": hourly.get("nitrogen_dioxide", [None] * len(times))[i],
            "sulphur_dioxide": hourly.get("sulphur_dioxide", [None] * len(times))[i],
            "ozone": hourly.get("ozone", [None] * len(times))[i],
            "_collected_at": collected_at,  # usage interne, pas exporté dans le CSV final
        }
        rows.append(row)
    return rows


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(RAW_DIR.glob("*/*.json"))
    if not raw_files:
        print(f"Aucun fichier brut trouvé dans {RAW_DIR}. Lancez collect.py ou backfill.py d'abord.")
        return

    print(f"Lecture de {len(raw_files)} fichiers bruts...")

    # dédup : clé = (city, timestamp_utc), on garde la ligne dont _collected_at est le plus récent
    deduped = {}
    n_rows_seen = 0

    for path in raw_files:
        try:
            rows = parse_raw_file(path)
        except Exception as exc:
            print(f"  [!] fichier ignoré (invalide) : {path} -> {exc}")
            continue

        for row in rows:
            n_rows_seen += 1
            key = (row["city"], row["timestamp_utc"])
            existing = deduped.get(key)
            if existing is None or row["_collected_at"] > existing["_collected_at"]:
                deduped[key] = row

    # tri chronologique (ville puis timestamp, pour un fichier lisible et stable)
    final_rows = sorted(deduped.values(), key=lambda r: (r["city"], r["timestamp_utc"]))

    with open(CLEAN_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in final_rows:
            writer.writerow(row)

    print(f"Lignes brutes lues     : {n_rows_seen}")
    print(f"Lignes après dédup     : {len(final_rows)}")
    print(f"Fichier clean écrit    : {CLEAN_FILE}")


if __name__ == "__main__":
    main()
