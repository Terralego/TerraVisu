web: gunicorn project.wsgi:application -w 1 --bind 0.0.0.0:8000
worker: celery -A project worker -c 1 -l info
beat: celery -A project beat -l info
release: sh /opt/release.sh
