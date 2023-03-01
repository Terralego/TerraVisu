#!/usr/bin/env bash

# Migrate database
python ./manage.py migrate --noinput
# Collect static files
python ./manage.py collectstatic --noinput