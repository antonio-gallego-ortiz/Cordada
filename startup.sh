#!/usr/bin/env bash
# Script de arranque para Azure App Service (Linux).
set -o errexit

python manage.py collectstatic --no-input
python manage.py migrate

gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout 120 cordada.wsgi:application
