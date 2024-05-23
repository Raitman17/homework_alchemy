#!/bin/bash

alembic upgrade head

exec python3 -m gunicorn --bind 0.0.0.0:5000 --workers=4 app:app