"""
Configuration commune : URL API, variables horaires demandées, chemins.
Aucun secret ici : tout ce qui est sensible passe par les variables
d'environnement (voir .env.example).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Documentation : https://open-meteo.com/en/docs/air-quality-api
AIR_QUALITY_API_URL = os.getenv(
    "AIR_QUALITY_API_URL", "https://air-quality-api.open-meteo.com/v1/air-quality"
)

HOURLY_VARIABLES = [
    "european_aqi",
    "us_aqi",
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
]

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = Path(os.getenv("RAW_DIR", BASE_DIR / "data" / "raw"))
CLEAN_DIR = Path(os.getenv("CLEAN_DIR", BASE_DIR / "data" / "clean"))
CLEAN_FILE = CLEAN_DIR / "clean_aqi.csv"

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "sslmode": os.getenv("DB_SSLMODE", "require"),
}