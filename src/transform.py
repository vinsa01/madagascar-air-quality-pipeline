"""
transform.py — Reconstruit clean/clean_aqi.csv EN ENTIER à partir de data/raw/.

Principe : raw/ est la source de vérité. Ce script ne fait que relire tous les
fichiers bruts, aplatir chaque (ville, heure) en une ligne, dédupliquer sur
(ville, timestamp) en gardant la mesure la plus récemment collectée, trier
chronologiquement, et réécrire le CSV depuis zéro.

Gestion :
- nulls (valeurs manquantes de l'API → None)
- types (float / int)
- outliers extrêmes → None
- normalisation des timestamps (formats proches → ISO UTC)
- rejet des timestamps impossibles à interpréter
- déduplication stricte (city + timestamp_utc)

Utilisation :
    python src/transform.py
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import RAW_DIR, CLEAN_DIR, CLEAN_FILE
from validate import main as validate_clean

FIELDNAMES = [
    "city", "country", "latitude", "longitude", "timestamp_utc",
    "european_aqi", "us_aqi", "pm10", "pm2_5",
    "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone",
]

# Bornes raisonnables pour détecter les valeurs aberrantes
OUTLIER_BOUNDS = {
    "pm10": (0, 1000),
    "pm2_5": (0, 500),
    "carbon_monoxide": (0, 50000),
    "nitrogen_dioxide": (0, 1000),
    "sulphur_dioxide": (0, 1000),
    "ozone": (0, 500),
    "european_aqi": (0, 300),
    "us_aqi": (0, 500),
}

def to_float(value):
    """Convertit en float ou retourne None si impossible / null."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value):
    """Convertit en int ou retourne None."""
    if value is None:
        return None
    try:
        return int(float(value))  # gère 42.0 → 42
    except (TypeError, ValueError):
        return None


def clean_numeric(value, col_name: str):
    """Applique typage + filtre outlier."""
    if col_name in ("european_aqi", "us_aqi"):
        num = to_int(value)
    else:
        num = to_float(value)

    if num is None:
        return None

    bounds = OUTLIER_BOUNDS.get(col_name)
    if bounds and not (bounds[0] <= num <= bounds[1]):
        return None  # outlier extrême → None

    return num


def normalize_timestamp(ts):
    """
    Normalise un timestamp en ISO UTC (YYYY-MM-DDTHH:MM:SS).
    Retourne la string normalisée ou None si impossible à interpréter.
    """
    if not ts or not isinstance(ts, str):
        return None

    ts = ts.strip()

    # Formats les plus fréquents (Open-Meteo + variantes courantes)
    formats = (
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    )

    for fmt in formats:
        try:
            dt = datetime.strptime(ts, fmt)
            # Pas de fuseau → on considère UTC (comme demandé à l'API)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue

    # Dernier essai avec fromisoformat (gère certains cas modernes)
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except (ValueError, TypeError):
        return None


def parse_raw_file(path: Path):
    """Transforme un fichier JSON brut (1 ville, 1 appel) en liste de lignes plates."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    meta = raw["_meta"]
    api = raw["api_response"]
    hourly = api.get("hourly", {})
    times = hourly.get("time", [])

    collected_at = meta["collected_at_utc"]
    n = len(times)

    rows = []
    for i, ts in enumerate(times):
        ts_clean = normalize_timestamp(ts)
        if ts_clean is None:
            continue  # timestamp illisible → on ignore la ligne

        row = {
            "city": meta["city"],
            "country": meta["country"],
            "latitude": to_float(api.get("latitude", meta.get("requested_latitude"))),
            "longitude": to_float(api.get("longitude", meta.get("requested_longitude"))),
            "timestamp_utc": ts_clean,
            "european_aqi": clean_numeric(
                hourly.get("european_aqi", [None] * n)[i], "european_aqi"
            ),
            "us_aqi": clean_numeric(
                hourly.get("us_aqi", [None] * n)[i], "us_aqi"
            ),
            "pm10": clean_numeric(hourly.get("pm10", [None] * n)[i], "pm10"),
            "pm2_5": clean_numeric(hourly.get("pm2_5", [None] * n)[i], "pm2_5"),
            "carbon_monoxide": clean_numeric(
                hourly.get("carbon_monoxide", [None] * n)[i], "carbon_monoxide"
            ),
            "nitrogen_dioxide": clean_numeric(
                hourly.get("nitrogen_dioxide", [None] * n)[i], "nitrogen_dioxide"
            ),
            "sulphur_dioxide": clean_numeric(
                hourly.get("sulphur_dioxide", [None] * n)[i], "sulphur_dioxide"
            ),
            "ozone": clean_numeric(hourly.get("ozone", [None] * n)[i], "ozone"),
            "_collected_at": collected_at,  # interne uniquement (pas exporté)
        }
        rows.append(row)

    return rows

def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(RAW_DIR.glob("*/*.json"))
    if not raw_files:
        print(f"Aucun fichier brut trouvé dans {RAW_DIR}.")
        print("Lancez d'abord extract.py ou backfill.py.")
        return

    print(f"Lecture de {len(raw_files)} fichiers bruts...")

    deduped = {}
    n_rows_seen = 0
    n_invalid_files = 0
    n_skipped_ts = 0

    for path in raw_files:
        try:
            rows = parse_raw_file(path)
        except Exception as exc:
            print(f"  [!] fichier ignoré (invalide) : {path.name} → {exc}")
            n_invalid_files += 1
            continue

        for row in rows:
            # Clé primaire obligatoire
            if not row["city"] or not row["timestamp_utc"]:
                n_skipped_ts += 1
                continue

            n_rows_seen += 1
            key = (row["city"], row["timestamp_utc"])
            existing = deduped.get(key)

            # Garde la collecte la plus récente
            if existing is None or row["_collected_at"] > existing["_collected_at"]:
                deduped[key] = row

    # Tri chronologique (ville puis timestamp)
    final_rows = sorted(
        deduped.values(),
        key=lambda r: (r["city"], r["timestamp_utc"])
    )

    # Écriture du CSV final (sans la colonne interne _collected_at)
    with open(CLEAN_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in final_rows:
            writer.writerow(row)

    print(f"Fichiers invalides          : {n_invalid_files}")
    print(f"Lignes brutes retenues      : {n_rows_seen}")
    print(f"Lignes après déduplication  : {len(final_rows)}")
    print(f"Fichier clean écrit         : {CLEAN_FILE}")

if __name__ == "__main__":
    main()
    validate_clean()