#!/bin/bash

set -e

for target in $WAIT_TARGETS
do
  ./wait-for-it.sh "$target"
done

if [[ "$1" = 'server' ]]; then
  if [[ "$DEBUG" != '' ]]; then
    set -- python manage.py runserver_plus 0.0.0.0:8000
  else
    set -- python main.py
  fi
elif [[ "$1" = 'worker' ]]; then
  set -- celery -A conf worker -l info
elif [[ "$1" = 'scheduler' ]]; then
  set -- celery -A conf beat -l info -S django
fi

exec "$@"
