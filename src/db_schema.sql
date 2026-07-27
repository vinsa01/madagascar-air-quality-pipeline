-- ============================================================
-- Data warehouse "qualité de l'air" — schéma en étoile
-- Respecte les règles du cours :
--   - aucune mesure dans les dimensions
--   - aucune colonne descriptive dans la table de faits
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_city (
    city_id     SERIAL PRIMARY KEY,
    city_name   VARCHAR(100) NOT NULL,
    country     VARCHAR(100) NOT NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    UNIQUE (city_name, country)
);

CREATE TABLE IF NOT EXISTS dim_time (
    time_id         BIGINT PRIMARY KEY,          -- format AAAAMMJJHH, ex: 2026072514
    full_timestamp  TIMESTAMP NOT NULL,           -- horodatage UTC complet
    date            DATE NOT NULL,
    year            SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    day             SMALLINT NOT NULL,
    hour            SMALLINT NOT NULL,
    day_of_week     VARCHAR(10) NOT NULL,          -- ex: 'Monday'
    day_of_week_num SMALLINT NOT NULL,             -- 0 = lundi ... 6 = dimanche
    is_weekend      BOOLEAN NOT NULL,
    UNIQUE (full_timestamp)
);

CREATE TABLE IF NOT EXISTS fact_aqi (
    fact_id             BIGSERIAL PRIMARY KEY,
    city_id             INTEGER NOT NULL REFERENCES dim_city(city_id),
    time_id             BIGINT NOT NULL REFERENCES dim_time(time_id),

    -- mesures uniquement (aucune colonne descriptive)
    european_aqi        DOUBLE PRECISION,
    us_aqi               DOUBLE PRECISION,
    pm10                DOUBLE PRECISION,
    pm2_5                DOUBLE PRECISION,
    carbon_monoxide     DOUBLE PRECISION,
    nitrogen_dioxide    DOUBLE PRECISION,
    sulphur_dioxide     DOUBLE PRECISION,
    ozone               DOUBLE PRECISION,

    UNIQUE (city_id, time_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_aqi_city ON fact_aqi(city_id);
CREATE INDEX IF NOT EXISTS idx_fact_aqi_time ON fact_aqi(time_id);
