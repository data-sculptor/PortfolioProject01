#!/usr/bin/env bash
set -euo pipefail

KAFKA_BROKER_HOST=${KAFKA_BROKER_HOST:-localhost}
KAFKA_BROKER_PORT=${KAFKA_BROKER_PORT:-9092}
TOPIC_NAME=${KAFKA_TOPIC:-nyc_taxi_trips}
PARTITIONS=${PARTITIONS:-3}
REPLICATION=${REPLICATION:-1}

docker compose exec -T kafka kafka-topics \
  --create \
  --if-not-exists \
  --topic "$TOPIC_NAME" \
  --bootstrap-server ${KAFKA_BROKER_HOST}:${KAFKA_BROKER_PORT} \
  --partitions $PARTITIONS \
  --replication-factor $REPLICATION || true

docker compose exec -T kafka kafka-topics \
  --list \
  --bootstrap-server ${KAFKA_BROKER_HOST}:${KAFKA_BROKER_PORT}

echo "Topic ensured: $TOPIC_NAME"


