"""
load.py — Charge clean/clean_aqi.csv dans le data warehouse Postgres.

Rejouable et idempotent :
  - crée le schéma (dim_city, dim_time, fact_aqi) s'il n'existe pas encore
  - upsert des dimensions (ON CONFLICT DO NOTHING / DO UPDATE)
  - upsert de la table de faits sur (city_id, time_id), donc relancer le
    script après un nouveau run de collecte ne duplique jamais les lignes

Nécessite les variables d'environnement décrites dans .env.example
(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSLMODE).

Utilisation :
    python src/load.py
"""
import csv
from datetime import datetime
from pathlib import Path

import psycopg

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_CONFIG, CLEAN_FILE
from cities import CITIES


def get_connection():
    missing = [k for k, v in DB_CONFIG.items() if v in (None, "") and k != "sslmode"]
    if missing:
        raise RuntimeError(
            f"Variables d'environnement manquantes pour la connexion DB : {missing}. "
            "Copiez .env.example vers .env et complétez-le."
        )
    return psycopg.connect(**DB_CONFIG)


def ensure_schema(conn):
    schema_path = Path(__file__).resolve().parent / "db_schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        ddl = f.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("Schéma vérifié / créé.")


def upsert_cities(conn):
    """Charge la dimension ville depuis cities.py (la source de vérité)."""
    with conn.cursor() as cur:
        for c in CITIES:
            cur.execute(
                """
                INSERT INTO dim_city (city_name, country, latitude, longitude)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (city_name, country) DO UPDATE
                    SET latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude
                """,
                (c["city"], c["country"], c["latitude"], c["longitude"]),
            )
    conn.commit()
    print(f"{len(CITIES)} villes chargées dans dim_city.")


def get_city_id_map(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT city_id, city_name FROM dim_city")
        return {name: cid for cid, name in cur.fetchall()}


def build_time_row(ts: datetime):
    time_id = int(ts.strftime("%Y%m%d%H"))
    return {
        "time_id": time_id,
        "full_timestamp": ts,
        "date": ts.date(),
        "year": ts.year,
        "month": ts.month,
        "day": ts.day,
        "hour": ts.hour,
        "day_of_week": ts.strftime("%A"),
        "day_of_week_num": ts.weekday(),
        "is_weekend": ts.weekday() >= 5,
    }


def load_csv_rows():
    if not CLEAN_FILE.exists():
        return []
    with open(CLEAN_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def upsert_time_and_facts(conn, rows, city_id_map):
    time_rows = {}
    fact_rows = []

    for row in rows:
        ts = datetime.fromisoformat(row["timestamp_utc"])
        trow = build_time_row(ts)
        time_rows[trow["time_id"]] = trow

        city_id = city_id_map.get(row["city"])
        if city_id is None:
            print(f"  [!] ville inconnue dans dim_city, ligne ignorée : {row['city']}")
            continue

        fact_rows.append((
            city_id,
            trow["time_id"],
            _to_float(row["european_aqi"]),
            _to_float(row["us_aqi"]),
            _to_float(row["pm10"]),
            _to_float(row["pm2_5"]),
            _to_float(row["carbon_monoxide"]),
            _to_float(row["nitrogen_dioxide"]),
            _to_float(row["sulphur_dioxide"]),
            _to_float(row["ozone"]),
        ))

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO dim_time (time_id, full_timestamp, date, year, month, day,
                                   hour, day_of_week, day_of_week_num, is_weekend)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (time_id) DO NOTHING
            """,
            [
                (t["time_id"], t["full_timestamp"], t["date"], t["year"], t["month"],
                 t["day"], t["hour"], t["day_of_week"], t["day_of_week_num"], t["is_weekend"])
                for t in time_rows.values()
            ],
        )
        conn.commit()
        print(f"{len(time_rows)} lignes upsertées dans dim_time.")

        cur.executemany(
            """
            INSERT INTO fact_aqi (city_id, time_id, european_aqi, us_aqi, pm10, pm2_5,
                                   carbon_monoxide, nitrogen_dioxide, sulphur_dioxide, ozone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (city_id, time_id) DO UPDATE SET
                european_aqi = EXCLUDED.european_aqi,
                us_aqi = EXCLUDED.us_aqi,
                pm10 = EXCLUDED.pm10,
                pm2_5 = EXCLUDED.pm2_5,
                carbon_monoxide = EXCLUDED.carbon_monoxide,
                nitrogen_dioxide = EXCLUDED.nitrogen_dioxide,
                sulphur_dioxide = EXCLUDED.sulphur_dioxide,
                ozone = EXCLUDED.ozone
            """,
            fact_rows,
        )
        conn.commit()
        print(f"{len(fact_rows)} lignes upsertées dans fact_aqi.")


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def main():
    conn = get_connection()
    try:
        ensure_schema(conn)
        upsert_cities(conn)

        rows = load_csv_rows()
        if not rows:
            print(f"\n{CLEAN_FILE} est vide ou introuvable : schéma et villes créés, "
                  f"mais aucune mesure chargée. Lancez extract.py / backfill.py puis "
                  f"transform.py, puis relancez ce script.")
            return

        city_id_map = get_city_id_map(conn)
        upsert_time_and_facts(conn, rows, city_id_map)
        print("\nChargement du warehouse terminé avec succès.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()