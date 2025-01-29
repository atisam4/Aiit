#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Try to use gunicorn first, fallback to waitress
if command -v gunicorn &> /dev/null; then
    gunicorn app:app
else
    python -m waitress --port=${PORT:-8000} app:app
fi
