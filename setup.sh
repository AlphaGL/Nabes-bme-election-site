#!/bin/bash
# Build/setup script.
#
# On Vercel: run automatically as the @vercel/static-build step in
# vercel.json — installs dependencies and collects static files into
# staticfiles_build/static so vercel.json's /static/(.*) route can serve them.
#
# Locally: run manually (`bash setup.sh`) to install dependencies and
# collect static files the same way, before `python manage.py runserver`.
#
# Does NOT run database migrations — those touch the live shared database
# and should be run deliberately (`python manage.py migrate`), not on every
# build/deploy.

set -e

echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear
