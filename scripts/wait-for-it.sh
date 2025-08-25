#!/usr/bin/env bash
# Minimal wait-for-it replacement
set -e
HOST=${1:-localhost}
PORT=${2:-5432}
TIMEOUT=${3:-60}

echo "Waiting for ${HOST}:${PORT} ..."
SECONDS=0
until nc -z ${HOST} ${PORT}; do
  sleep 1
  if [ $SECONDS -ge $TIMEOUT ]; then
    echo "Timeout waiting for ${HOST}:${PORT}"
    exit 1
  fi
done
echo "${HOST}:${PORT} is up"


