#!/usr/bin/env bash
set -e

ENV_FILE="/app/.env"
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' $ENV_FILE | xargs) || true
fi

if [ -n "$DATABASE_HOST" ]; then
  echo "Waiting for Postgres at $DATABASE_HOST:$DATABASE_PORT..."
  until nc -z "$DATABASE_HOST" "${DATABASE_PORT:-5432}"; do
    sleep 0.5
  done
fi


echo "Running migrations..."
python /app/src/manage.py migrate --noinput


echo "Collecting static files..."
python /app/src/manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Creating superuser..."
  python /app/src/manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); \
username='${DJANGO_SUPERUSER_USERNAME}'; email='${DJANGO_SUPERUSER_EMAIL}'; password='${DJANGO_SUPERUSER_PASSWORD}'; \
u = None
try:
    u = User.objects.filter(username=username).first()
except Exception:
    pass
if not u:
    User.objects.create_superuser(username, email, password)"
fi

exec "$@"
