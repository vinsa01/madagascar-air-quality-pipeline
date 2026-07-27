"""
collect.py — Collecte "live" horaire.

Appelle l'API Open-Meteo pour chaque ville, sur une petite fenêtre récente
(past_hours=48 par défaut) pour être tolérant aux runs manqués, et écrit
UN fichier JSON brut par ville et par appel dans data/raw/.

Ce script ne modifie JAMAIS un fichier existant : chaque exécution crée de
nouveaux fichiers horodatés. C'est la garantie de "raw/ intouchable".

Utilisation :
    python src/collect.py
"""
import json
import sys
import time
from datetime import datetime, timezone

import requests

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cities import CITIES
from config import AIR_QUALITY_API_URL, HOURLY_VARIABLES, RAW_DIR

PAST_HOURS = 48  # fenêtre de sécurité : couvre les runs manqués sans faire de trous
MAX_RETRIES = 3


def fetch_city(city: dict, past_hours: int = PAST_HOURS) -> dict:
    """Appelle l'API pour une ville et renvoie le JSON brut (+ métadonnées)."""
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": ",".join(HOURLY_VARIABLES),
        "past_hours": past_hours,
        "forecast_hours": 1,
        "timezone": "UTC",
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(AIR_QUALITY_API_URL, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            return {
                "_meta": {
                    "city": city["city"],
                    "country": city["country"],
                    "requested_latitude": city["latitude"],
                    "requested_longitude": city["longitude"],
                    "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                    "source_url": resp.url,
                },
                "api_response": payload,
            }
        except requests.RequestException as exc:
            last_error = exc
            print(f"  [!] tentative {attempt}/{MAX_RETRIES} échouée pour {city['city']}: {exc}")
            time.sleep(2 * attempt)

    raise RuntimeError(f"Échec de collecte pour {city['city']} après {MAX_RETRIES} tentatives") from last_error


def save_raw(city_name: str, data: dict) -> str:
    """Écrit le JSON brut dans data/raw/<ville>/<ville>_<timestamp>.json"""
    city_dir = RAW_DIR / city_name
    city_dir.mkdir(parents=True, exist_ok=True)

    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = city_dir / f"{city_name}_{run_ts}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(out_path)


def main():
    print(f"=== Collecte horaire — {datetime.now(timezone.utc).isoformat()} ===")
    failures = []

    for city in CITIES:
        print(f"-> {city['city']}")
        try:
            data = fetch_city(city)
            path = save_raw(city["city"], data)
            print(f"   OK -> {path}")
        except Exception as exc:  # noqa: BLE001
            print(f"   ECHEC : {exc}")
            failures.append(city["city"])

    if failures:
        print(f"\nVilles en échec : {failures}")
        sys.exit(1)  # code non-zéro -> le run Airflow apparaît en échec

    print("\nCollecte terminée avec succès pour toutes les villes.")


if __name__ == "__main__":
    main()
