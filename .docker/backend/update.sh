#!/usr/bin/env bash

# Migrate database
python ./manage.py migrate --noinput

# Collect static files
python ./manage.py collectstatic --noinput

# Collect admin static files if prod image
if [ -d "/opt/frontend" ];
then
  # Delete previous frontend files
  echo "Deleting previous frontend static files"
  find /opt/terra-visu/public -maxdepth 1 -type f -exec rm {} \;
  rm -r /opt/terra-visu/public/static /opt/terra-visu/public/images /opt/terra-visu/public/locales /opt/terra-visu/admin
  echo "Collect frontend static files"
  cp -r /opt/frontend/* /opt/terra-visu/public/
fi