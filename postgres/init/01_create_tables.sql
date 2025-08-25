CREATE TABLE IF NOT EXISTS fact_trips (
  trip_id BIGSERIAL PRIMARY KEY,
  vendor_id TEXT,
  pickup_datetime TIMESTAMP,
  dropoff_datetime TIMESTAMP,
  passenger_count INT,
  trip_distance DOUBLE PRECISION,
  pickup_longitude DOUBLE PRECISION,
  pickup_latitude DOUBLE PRECISION,
  dropoff_longitude DOUBLE PRECISION,
  dropoff_latitude DOUBLE PRECISION,
  fare_amount DOUBLE PRECISION,
  extra DOUBLE PRECISION,
  mta_tax DOUBLE PRECISION,
  tip_amount DOUBLE PRECISION,
  tolls_amount DOUBLE PRECISION,
  total_amount DOUBLE PRECISION,
  payment_type TEXT,
  rate_code TEXT,
  store_and_fwd_flag TEXT,
  pickup_date DATE GENERATED ALWAYS AS (DATE(pickup_datetime)) STORED
);

CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_date ON fact_trips (pickup_date);
CREATE INDEX IF NOT EXISTS idx_fact_trips_payment_type ON fact_trips (payment_type);

CREATE TABLE IF NOT EXISTS agg_daily_metrics (
  pickup_date DATE,
  vendor_id TEXT,
  payment_type TEXT,
  trips_count BIGINT,
  total_revenue DOUBLE PRECISION,
  avg_trip_distance DOUBLE PRECISION,
  PRIMARY KEY (pickup_date, vendor_id, payment_type)
);


