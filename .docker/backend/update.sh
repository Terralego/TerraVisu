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
      rm -r /opt/terra-visu/public/admin
  fi

  cp -r /opt/admin /opt/terra-visu/public/
fi