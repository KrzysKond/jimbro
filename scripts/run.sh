#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate

daphne -b 0.0.0.0 -p 9000 app.asgi:application &

python manage.py runworker