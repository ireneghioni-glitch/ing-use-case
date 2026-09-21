from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from marketing_spy.generate_candidate_urls import (
    generate_candidate_urls,
)


with DAG(
    dag_id="marketing_spy_url_discovery",

    start_date=datetime(
        2026,
        9,
        1,
    ),

    schedule="0 3 * * 1",

    catchup=False,

    tags=[
        "marketing-spy",
        "url-discovery",
    ],
) as dag:

    generate_urls = PythonOperator(
        task_id="generate_candidate_urls",

        python_callable=generate_candidate_urls,
    )