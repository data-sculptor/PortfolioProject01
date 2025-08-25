# Power BI Model: NYC Taxi Portfolio

Data source: Postgres (host `localhost`, db `nyc_taxi`, user `postgres`, password `postgres`).

Tables:
- fact_trips
- agg_daily_metrics

Recommended relationships:
- None required; use tables independently. Optionally create a date table and relate `Date[date]` to `agg_daily_metrics[pickup_date]`.

Key measures (DAX examples):
- Trips = SUM(agg_daily_metrics[trips_count])
- Revenue = SUM(agg_daily_metrics[total_revenue])
- Avg Trip Distance = AVERAGE(agg_daily_metrics[avg_trip_distance])

Suggested visuals:
- Card: Trips, Revenue, Avg Trip Distance (filterable by date range)
- Line chart: Trips by pickup_date
- Bar chart: Revenue by payment_type
- Heatmap (matrix): Trips by vendor_id and payment_type
- Map: Optional if geospatial table is added later

Slicers:
- Date range
- Vendor
- Payment Type

Refresh strategy:
- DirectQuery or Scheduled import from Postgres (e.g., hourly)


