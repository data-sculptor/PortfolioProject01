import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    TimestampType,
    IntegerType,
    DoubleType,
)


def get_schema():
    return StructType([
        StructField("vendor_id", StringType()),
        StructField("pickup_datetime", TimestampType()),
        StructField("dropoff_datetime", TimestampType()),
        StructField("passenger_count", IntegerType()),
        StructField("trip_distance", DoubleType()),
        StructField("pickup_longitude", DoubleType()),
        StructField("pickup_latitude", DoubleType()),
        StructField("dropoff_longitude", DoubleType()),
        StructField("dropoff_latitude", DoubleType()),
        StructField("fare_amount", DoubleType()),
        StructField("extra", DoubleType()),
        StructField("mta_tax", DoubleType()),
        StructField("tip_amount", DoubleType()),
        StructField("tolls_amount", DoubleType()),
        StructField("total_amount", DoubleType()),
        StructField("payment_type", StringType()),
        StructField("rate_code", StringType()),
        StructField("store_and_fwd_flag", StringType()),
    ])


def foreach_batch(df, epoch_id):
    jdbc_url = (
        f"jdbc:postgresql://{os.environ.get('POSTGRES_HOST', 'postgres')}:{os.environ.get('POSTGRES_PORT', '5432')}/"
        f"{os.environ.get('POSTGRES_DB', 'nyc_taxi')}"
    )
    properties = {
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "driver": "org.postgresql.Driver",
    }

    df.write.mode("append").jdbc(jdbc_url, "fact_trips", properties=properties)


def main():
    spark = (
        SparkSession.builder.appName(os.environ.get("SPARK_APP_NAME", "nyc-taxi-streaming"))
        .getOrCreate()
    )

    kafka_servers = os.environ.get("KAFKA_BROKERS", "kafka:29092")
    topic = os.environ.get("KAFKA_TOPIC", "nyc_taxi_trips")
    checkpoint = os.environ.get("SPARK_CHECKPOINT_DIR", "/opt/spark/checkpoints/nyc_taxi")

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_servers)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .load()
    )

    schema = get_schema()
    parsed = raw.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    cleaned = parsed.dropna(subset=["pickup_datetime", "dropoff_datetime"]).filter(col("trip_distance") >= 0)

    query = (
        cleaned.writeStream.outputMode("append")
        .foreachBatch(foreach_batch)
        .option("checkpointLocation", checkpoint)
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()


