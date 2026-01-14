#!/bin/sh
set -e

DB_HOST="${MYSQL_HOST:-db}"
DB_PORT="${MYSQL_PORT:-3306}"

echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT}..."
for i in $(seq 1 60); do
  if nc -z "$DB_HOST" "$DB_PORT"; then
    echo "MySQL port is open!"
    break
  fi
  echo "Still waiting (${i}/60)..."
  sleep 1
done

# Si après 60s ça ne répond toujours pas => stop
if ! nc -z "$DB_HOST" "$DB_PORT"; then
  echo "MySQL not reachable after 60s."
  exit 1
fi

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static..."
python manage.py collectstatic --noinput || true

exec "$@"
