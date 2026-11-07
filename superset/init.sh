#!/bin/sh
set -eu
superset db upgrade
python /app/pythonpath/bootstrap_admin.py
superset init
exec /usr/bin/run-server.sh
