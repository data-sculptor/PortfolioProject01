# NYC Taxi Streaming & Batch ETL Portfolio (Kafka, Airflow, Spark, Postgres, BigQuery, Power BI)

This portfolio project demonstrates a modern data engineering stack combining streaming and batch processing:

- Kafka for streaming ingestion
- Airflow for orchestration
- Spark (Structured Streaming and batch) for transformation
- Postgres for serving layer and ad-hoc analytics
- BigQuery Public Datasets as the raw source
- Power BI for BI/visualization

The pipeline streams a subset of the BigQuery NYC Taxi Trips dataset into Kafka, processes it with Spark, stores curated data and aggregates in Postgres, and optionally writes aggregates back to BigQuery.

## High-Level Architecture

1. Airflow orchestrates a daily job to fetch yesterday's trips from BigQuery (public dataset), then produces them to a Kafka topic.
2. Spark Structured Streaming consumes the Kafka topic, parses JSON, cleanses/enriches, and writes:
   - Curated trips to Postgres (`fact_trips`)
   - Incremental aggregates to Postgres (`agg_daily_metrics`)
3. A batch Spark job (triggered by Airflow) recomputes daily aggregates over a larger horizon and can optionally publish to BigQuery for sharing.
4. Power BI connects to Postgres to visualize KPIs.

## Repository Layout

```
de-portfolio-nyctaxi/
  docker-compose.yml
  .env.example
  config/settings.yaml
  airflow/
    dags/nyc_taxi_etl.py
    requirements.txt
  kafka/
    topics.sh
    producer/
      producer.py
      requirements.txt
      config.yaml
  spark/
    docker/Dockerfile
    jobs/streaming_consumer.py
    jobs/batch_aggregations.py
    submit-scripts/
      submit_streaming.sh
      submit_batch.sh
  postgres/
    init/01_create_tables.sql
  bigquery/
    queries/extract_daily_trips.sql
    schema_trips.json
    service-account.json.example
  powerbi/model_description.md
  scripts/
    wait-for-it.sh
    create_kafka_topics.sh
```

## Prerequisites

- Docker Desktop
- A Google Cloud service account with BigQuery read access to public datasets (for local dev you can run the producer with BigQuery Anonymous access using `pandas-gbq`, but service account is recommended)
- Optional: `gcloud` CLI

## Quick Start

1) Copy environment template and configure variables

```
cp .env.example .env
```

Fill in Kafka, Postgres, Airflow, and BigQuery credentials if applicable.
If you will let Airflow run the producer, place your GCP service account at `kafka/producer/service-account.json`. Airflow is configured with `GOOGLE_APPLICATION_CREDENTIALS=/opt/airflow/producer/service-account.json`.

2) Build and start the stack

```
docker compose up -d --build
```

3) Initialize Kafka topics

```
bash scripts/create_kafka_topics.sh
```

4) Open UIs

- Airflow: http://localhost:8080 (user: `airflow`, password: `airflow`)
- Spark Master UI: http://localhost:8081
- Postgres: `localhost:5432` (user: `postgres`, password: `postgres`)
- PGAdmin: http://localhost:5050 (user: `admin@local`, password: `admin`)

5) Streaming job runs automatically

The `spark-streaming` service auto-starts and runs `streaming_consumer.py`, continuously consuming Kafka and writing to Postgres. Verify in the Spark Master UI (http://localhost:8081) that an application named `nyc-taxi-streaming` is active.

6) Trigger the Airflow DAG `nyc_taxi_etl`

Open Airflow at http://localhost:8080 (airflow/airflow) and trigger `nyc_taxi_etl`. It will:
- Ensure Kafka topic exists
- Run the Kafka producer (reads yesterday from BigQuery, publishes to Kafka)
- Submit the batch aggregation Spark job

## Data Flow Details

- Source: BigQuery public dataset `bigquery-public-data.new_york_taxi_trips.tlc_green_trips_2015` (as example; can be changed in config)
- Kafka Topic: `nyc_taxi_trips`
- Spark Streaming Output:
  - Postgres table `fact_trips`
  - Postgres table `agg_daily_metrics` (windowed aggregates)
- Batch Aggregation Output (optional):
  - Postgres upserts to `agg_daily_metrics`
  - Optional: BigQuery table `your_project.analytics.nyc_taxi_daily_metrics`

## Configuration

Global config lives in `config/settings.yaml`:

```yaml
project:
  name: nyc-taxi-portfolio

bigquery:
  dataset: bigquery-public-data.new_york_taxi_trips
  table: tlc_green_trips_2015
  max_rows: 20000

kafka:
  broker: kafka:29092
  topic: nyc_taxi_trips

postgres:
  host: postgres
  port: 5432
  db: nyc_taxi
  user: postgres
  password: postgres

spark:
  app_name: nyc-taxi-streaming
  checkpoint_location: /opt/spark/checkpoints/nyc_taxi
```

Producer-specific config at `kafka/producer/config.yaml`.

Airflow has `GOOGLE_APPLICATION_CREDENTIALS` set to `/opt/airflow/producer/service-account.json`; put your service account file at `kafka/producer/service-account.json` on the host so it is mounted into the Airflow container.

## Airflow DAG

`airflow/dags/nyc_taxi_etl.py` defines:

- Extract: Query yesterday from BigQuery and write JSON lines to a temp file
- Load: Stream file into Kafka (producer)
- Batch Aggregate: Submit Spark batch job to compute daily aggregates

You can change schedule, tables, or limits via `Variable` or config files.

## Spark Jobs

- `streaming_consumer.py`:
  - Reads from Kafka using Structured Streaming
  - Parses JSON into columns
  - Cleans data, casts types, filters bad rows
  - Writes to Postgres with micro-batch foreachBatch upsert pattern

- `batch_aggregations.py`:
  - Reads curated table from Postgres
  - Computes daily aggregates by pickup_date, payment_type, vendor, etc.
  - Writes back to Postgres and (optionally) BigQuery

## Postgres Schema

Tables created in `postgres/init/01_create_tables.sql`:

- `fact_trips` (curated trip-level facts)
- `agg_daily_metrics` (day-level aggregates)

## Power BI

Connect Power BI Desktop to Postgres using the credentials in `.env`. The model and recommended visuals are described in `powerbi/model_description.md`.

## Environment Variables

See `.env.example` for overridable variables used by services and jobs.

## Local Development Notes

- To run the Kafka producer locally (instead of Airflow):

```
pip install -r kafka/producer/requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=./kafka/producer/service-account.json
python kafka/producer/producer.py --date 2015-01-15 --limit 5000
```

- The streaming consumer is already a long-running service (`spark-streaming`). If you do need to run it manually:

```
docker compose run --rm spark-submit \
  /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3 \
  /opt/spark/jobs/streaming_consumer.py
```

If you see "no configuration file provided" when running compose commands, ensure you are in the project directory (`de-portfolio-nyctaxi`) or pass `-f /absolute/path/to/docker-compose.yml`.

If you see "Missing application resource" from spark-submit, ensure the path `/opt/spark/jobs/streaming_consumer.py` exists inside the container. In this project it is mounted via `./spark/jobs:/opt/spark/jobs`.

If the producer fails with BigQuery auth errors, verify the service account JSON file exists at `kafka/producer/service-account.json` and that the account has BigQuery Viewer on the public dataset project.

If Postgres writes fail, verify tables exist (created by `postgres/init/01_create_tables.sql`) and the JDBC driver is available (we pass `org.postgresql:postgresql:42.7.3` in `--packages`).

If Kafka topic is missing, re-run `bash scripts/create_kafka_topics.sh`.

If Airflow webserver isn't up, inspect logs with `docker compose logs airflow | tail -n 200`.

## Rationale and Real-World Adjustments

Why these components:
- Kafka: durable, scalable ingestion for streaming; decouples producers and consumers.
- Airflow: mature orchestrator for dependency management, scheduling, retries, observability.
- Spark: unified engine for both streaming (Structured Streaming) and batch analytics.
- Postgres: convenient serving/analytics store for BI demos; easy to run locally.
- BigQuery Public Datasets: rich, realistic source without standing up external data infra.
- Power BI: common enterprise BI tool to visualize KPIs from serving layer.

What’s simplified here vs. production:
- Single-broker Kafka and no Schema Registry; in prod use multi-broker, Schema Registry, and possibly Kafka Connect for sinks.
- Airflow LocalExecutor; in prod use Celery/Kubernetes Executors and external metadata DB.
- Spark standalone with a single worker; in prod use Kubernetes/YARN with autoscaling, monitoring, and checkpoint storage on durable volumes (e.g., cloud buckets).
- Credentials as files and env vars; in prod use Secret Managers (GCP Secret Manager, Vault, etc.).
- JDBC overwrite for aggregates; in prod implement idempotent upserts via staging tables, MERGE, or use a storage layer that supports ACID merges (e.g., Delta/Iceberg/Hudi).
- Postgres as serving layer; in prod consider a warehouse (BigQuery/Snowflake) or lakehouse for large-scale analytics, and possibly a read-optimized store for APIs.

Operational considerations:
- Monitoring & alerting (Airflow SLAs, Spark metrics, Kafka lag).
- Backfills via Airflow params; configure DAG to iterate dates and control volume (`BIGQUERY_MAX_ROWS`).
- Data quality checks (e.g., Great Expectations) before publishing to serving tables.
- CI/CD: lint DAGs/jobs, test locally, deploy via pipelines.


## Cleanup

```
docker compose down -v
```

## Future Enhancements

- Add Kafka Connect sink to Postgres
- Add dbt transformations on top of Postgres
- Terraform for GCP infra and service accounts


