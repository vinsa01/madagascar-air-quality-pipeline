"""
DAG Airflow pour le backfill historique.

Contrairement au pipeline horaire, celui-ci n'a PAS de planification
automatique (schedule_interval=None) : c'est une opération ponctuelle que
vous déclenchez manuellement depuis l'UI Airflow une fois (ou après avoir
étendu la période). Il reste rejouable sans risque (backfill.py ignore les
mois déjà téléchargés).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "groupe-aqi-madagascar",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="air_quality_backfill",
    description="Backfill historique (12 mois) AQI -> raw/, puis reconstruction de clean/ et du warehouse",
    default_args=default_args,
    schedule_interval=None,  # déclenchement manuel uniquement
    start_date=datetime(2026, 7, 11),
    catchup=False,
    tags=["aqi", "madagascar", "backfill"],
) as dag:

    backfill = BashOperator(
        task_id="backfill",
        bash_command=f"cd {PROJECT_DIR}/src && python backfill.py --months 12",
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=f"cd {PROJECT_DIR}/src && python transform.py",
    )

    load_warehouse = BashOperator(
        task_id="load_warehouse",
        bash_command=f"cd {PROJECT_DIR}/src && python load_warehouse.py",
    )

    backfill >> transform >> load_warehouse
