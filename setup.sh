#!/bin/bash
# Local dev setup script. Not used by Vercel — the @vercel/python builder
# in vercel.json installs requirements.txt itself, and none of the
# templates currently reference local static files, so no separate
# static-build step is needed there.
#
# Run manually: `bash setup.sh`
#
# Does NOT run database migrations — those touch the live shared database
# and should be run deliberately (`python manage.py migrate`), not as part
# of routine setup.

set -e

echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear
