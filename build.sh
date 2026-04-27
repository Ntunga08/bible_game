#!/usr/bin/env bash
set -o errexit

python config/manage.py collectstatic --noinput
python config/manage.py migrate
