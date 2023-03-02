#!/usr/bin/env bash

# Migrate database
python ./manage.py migrate --noinput

# Collect static files
python ./manage.py collectstatic --noinput

# Collect admin static files if prod image
if [ -d "/opt/admin" ];
then
  # Delete previous admin if exists
  if [ -d "/opt/terra-visu/public/admin" ];
  then
      echo "Deleting previous admin static files"
      rm -r /opt/terra-visu/public/admin
  fi
  echo "Collect admin static files"
  cp -r /opt/admin /opt/terra-visu/public/
fi