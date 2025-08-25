import argparse
import json
import os
from datetime import datetime

import pandas as pd
from confluent_kafka import Producer
from pandas_gbq import read_gbq
import yaml


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def create_producer(broker: str) -> Producer:
    return Producer({"bootstrap.servers": broker})


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")


def read_bigquery(date_str: str, dataset: str, table: str, limit: int) -> pd.DataFrame:
    query = f"""
    SELECT
      vendor_id,
      pickup_datetime,
      dropoff_datetime,
      passenger_count,
      trip_distance,
      pickup_longitude,
      pickup_latitude,
      dropoff_longitude,
      dropoff_latitude,
      fare_amount,
      extra,
      mta_tax,
      tip_amount,
      tolls_amount,
      total_amount,
      payment_type,
      rate_code,
      store_and_fwd_flag
    FROM `{dataset}.{table}`
    WHERE DATE(pickup_datetime) = DATE('{date_str}')
    LIMIT {limit}
    """
    df = read_gbq(query, progress_bar_type=None)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=os.environ.get("PRODUCER_CONFIG", "config.yaml"))
    parser.add_argument("--date", default=(datetime.utcnow()).strftime("%Y-%m-%d"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    dataset = config["bigquery"]["dataset"]
    table = config["bigquery"]["table"]
    max_rows = config["bigquery"].get("max_rows", 20000)
    limit = args.limit or max_rows

    broker = config["kafka"]["broker"]
    topic = config["kafka"]["topic"]

    print(f"Reading BigQuery for date={args.date}, limit={limit}")
    df = read_bigquery(args.date, dataset, table, limit)
    print(f"Fetched {len(df)} rows")

    p = create_producer(broker)

    for _, row in df.iterrows():
        msg = row.to_dict()
        payload = json.dumps(msg, default=str)
        p.produce(topic, value=payload.encode("utf-8"), callback=delivery_report)
    p.flush()
    print("Produced all messages")


if __name__ == "__main__":
    main()


