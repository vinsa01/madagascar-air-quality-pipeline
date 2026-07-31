"""
backfill.py — Collecte historique rejouable.

Récupère, pour chaque ville, l'historique horaire entre une date de début et
aujourd'hui, en découpant en tranches mensuelles (l'API accepte des plages
plus larges, mais découper limite la taille des réponses et facilite les
reprises en cas d'échec partiel).

Chaque appel (1 ville x 1 mois) est sauvegardé comme un fichier brut distinct
dans data/raw/, exactement comme extract.py — cohérent avec la règle
"un fichier par ville et par appel".

Idempotent : si un fichier existe déjà pour une ville+mois donné, il n'est
PAS re-téléchargé (sauf --force). On peut donc relancer le script autant
de fois que nécessaire sans dupliquer les appels API.

Utilisation :
    python src/backfill.py --months 12
    python src/backfill.py --start-date 2025-07-01 --end-date 2026-07-25
    python src/backfill.py --months 3 --force   # re-télécharge tout
"""
import argparse
import json
import time
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cities import CITIES
from config import AIR_QUALITY_API_URL, HOURLY_VARIABLES, RAW_DIR

MAX_RETRIES = 3


def month_ranges(start_date: datetime, end_date: datetime):
    """Découpe [start_date, end_date] en tranches mensuelles (début, fin inclus)."""
    cursor = start_date
    while cursor < end_date:
        chunk_end = min(cursor + relativedelta(months=1) - relativedelta(days=1), end_date)
        yield cursor.date(), chunk_end.date()
        cursor = chunk_end + relativedelta(days=1)


def fetch_range(city: dict, start_date, end_date) -> dict:
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": ",".join(HOURLY_VARIABLES),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "timezone": "UTC",
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(AIR_QUALITY_API_URL, params=params, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            return {
                "_meta": {
                    "city": city["city"],
                    "country": city["country"],
                    "requested_latitude": city["latitude"],
                    "requested_longitude": city["longitude"],
                    "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                    "range_start": start_date.isoformat(),
                    "range_end": end_date.isoformat(),
                    "source_url": resp.url,
                },
                "api_response": payload,
            }
        except requests.RequestException as exc:
            last_error = exc
            print(f"    tentative {attempt}/{MAX_RETRIES} échouée : {exc}")
            time.sleep(2 * attempt)

    raise RuntimeError(f"Échec après {MAX_RETRIES} tentatives") from last_error


def main():
    parser = argparse.ArgumentParser(description="Backfill historique AQI")
    parser.add_argument("--months", type=int, default=12, help="Nombre de mois à récupérer (défaut: 12)")
    parser.add_argument("--start-date", type=str, default=None, help="Date de début YYYY-MM-DD (prioritaire sur --months)")
    parser.add_argument("--end-date", type=str, default=None, help="Date de fin YYYY-MM-DD (défaut: aujourd'hui)")
    parser.add_argument("--force", action="store_true", help="Re-télécharge même si le fichier existe déjà")
    args = parser.parse_args()

    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else datetime.now(timezone.utc)
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = end_date - relativedelta(months=args.months)

    print(f"=== Backfill du {start_date.date()} au {end_date.date()} ===")

    total_calls, skipped, failed = 0, 0, 0

    for city in CITIES:
        city_dir = RAW_DIR / city["city"]
        city_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n-> {city['city']}")

        for chunk_start, chunk_end in month_ranges(start_date, end_date):
            out_path = city_dir / f"{city['city']}_backfill_{chunk_start.isoformat()}_{chunk_end.isoformat()}.json"

            if out_path.exists() and not args.force:
                print(f"   [skip] {chunk_start} -> {chunk_end} (déjà présent)")
                skipped += 1
                continue

            print(f"   [fetch] {chunk_start} -> {chunk_end}")
            try:
                data = fetch_range(city, chunk_start, chunk_end)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                total_calls += 1
                time.sleep(0.5)
            except Exception as exc:
                print(f"   ECHEC : {exc}")
                failed += 1

    print(f"\n=== Terminé : {total_calls} appels réussis, {skipped} ignorés (déjà présents), {failed} échecs ===")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
