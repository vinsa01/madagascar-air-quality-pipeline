"""
DAG Airflow : pipeline AQI Madagascar.

Planification : toutes les heures, 24h/24.
Tâches : extract (API -> raw/) >> transform (raw/ -> clean/) >> load (clean/ -> warehouse)

En cas d'échec d'une tâche, Airflow retente automatiquement (voir default_args)
et le run apparaît en rouge dans l'UI -> c'est votre preuve d'exécution/échec
pour le rapport.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Chemin du projet à l'intérieur du conteneur/serveur Airflow.
# Adaptez PROJECT_DIR si votre repo est monté à un autre endroit.
PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "GROUPE 28",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="air_quality_pipeline",
    description="Collecte horaire AQI (5 villes Madagascar) -> clean -> data warehouse",
    default_args=default_args,
    schedule_interval="@hourly",
    start_date=datetime(2026, 7, 11),
    catchup=False,
    max_active_runs=1,
    tags=["aqi", "madagascar", "projet-data-engineering"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command=f"cd {PROJECT_DIR}/src && python extract.py",
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=f"cd {PROJECT_DIR}/src && python transform.py",
    )

    load = BashOperator(
        task_id="load",
        bash_command=f"cd {PROJECT_DIR}/src && python load.py",
    )

    extract >> transform >> load
