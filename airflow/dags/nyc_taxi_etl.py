from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


def default_args():
    return {
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }


def produce_to_kafka(execution_date: datetime, **_):
    import subprocess
    date_str = (execution_date or datetime.utcnow()).strftime("%Y-%m-%d")
    cmd = [
        "python",
        "/opt/airflow/producer/producer.py",
        "--config",
        "/opt/airflow/producer/config.yaml",
        "--date",
        date_str,
    ]
    env = os.environ.copy()
    subprocess.run(cmd, check=True, env=env)


with DAG(
    dag_id="nyc_taxi_etl",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args(),
) as dag:
    create_topics = BashOperator(
        task_id="create_kafka_topics",
        bash_command="bash /opt/airflow/scripts/create_kafka_topics.sh | cat",
    )

    produce = PythonOperator(
        task_id="produce_bq_to_kafka",
        python_callable=produce_to_kafka,
        op_kwargs={"execution_date": "{{ ds }}"},
    )

    submit_batch = BashOperator(
        task_id="spark_batch_aggregations",
        bash_command=(
            "/opt/bitnami/spark/bin/spark-submit "
            "--master spark://spark-master:7077 "
            "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3 "
            "/opt/spark/jobs/batch_aggregations.py"
        ),
    )

    create_topics >> produce >> submit_batch


