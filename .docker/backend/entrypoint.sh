#!/usr/bin/env bash

# Activate venv
. /opt/venv/bin/activate

# ensure folders exists
mkdir -p /opt/terra-visu/var/cache/sessions /opt/terra-visu/var/conf/templates /opt/terra-visu/var/conf/static

echo "Waiting for postgres..."
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    sleep 0.1
done
echo "PostgreSQL started"

# exec
exec "$@"
