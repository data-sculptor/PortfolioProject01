-- Parameter: @date (YYYY-MM-DD)
DECLARE target_date DATE DEFAULT @date;

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
FROM `bigquery-public-data.new_york_taxi_trips.tlc_green_trips_2015`
WHERE DATE(pickup_datetime) = target_date
LIMIT @limit;


