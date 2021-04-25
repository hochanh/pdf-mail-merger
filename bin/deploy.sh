#!/bin/sh
git pull origin master

npm ci
npm run build

poetry install
poetry run ./manage.py migrate
poetry run ./manage.py collectstatic --noinput

echo "Restarting gunicorn..."
lsof -ti :8001 | xargs kill || true
poetry run gunicorn --workers 1 --bind=0.0.0.0:8001 apps.wsgi:application --timeout 30 --daemon
echo "Gunicorn restarted!"
