#!/usr/bin/env bash
# exit on error
set -o errexit


pip install -r requirement.txt

python manage.py collectstatic --no-input
