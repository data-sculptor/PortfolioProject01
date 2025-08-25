import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, date_format, sum as _sum, avg as _avg, count as _count


def main():
    spark = SparkSession.builder.appName("nyc-taxi-batch").getOrCreate()

    jdbc_url = (
        f"jdbc:postgresql://{os.environ.get('POSTGRES_HOST', 'postgres')}:{os.environ.get('POSTGRES_PORT', '5432')}/"
        f"{os.environ.get('POSTGRES_DB', 'nyc_taxi')}"
    )
    properties = {
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "driver": "org.postgresql.Driver",
    }

    trips = spark.read.jdbc(jdbc_url, "fact_trips", properties=properties)

    agg = (
        trips.withColumn("pickup_date", date_format(col("pickup_datetime"), "yyyy-MM-dd"))
        .groupBy("pickup_date", "vendor_id", "payment_type")
        .agg(
            _count("*").alias("trips_count"),
            _sum("total_amount").alias("total_revenue"),
            _avg("trip_distance").alias("avg_trip_distance"),
        )
    )

    # Write to Postgres (merge-like behavior via overwrite on partition not available with JDBC easily; do append and rely on PK conflict outside spark or truncate+insert)
    # For simplicity, overwrite table each batch run. For production, upsert with staging tables.
    agg.write.mode("overwrite").jdbc(jdbc_url, "agg_daily_metrics", properties=properties)


if __name__ == "__main__":
    main()


