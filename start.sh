#!/bin/bash

# Give execute permission to the script
chmod +x start.sh

# Start supervisor (which manages Gunicorn)
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

# If supervisor fails, fallback to direct Gunicorn
if [ $? -ne 0 ]; then
    echo "Supervisor failed to start, falling back to direct Gunicorn..."
    gunicorn --workers 4 --bind 0.0.0.0:$PORT --timeout 120 --keep-alive 5 --log-level info --access-logfile - --error-logfile - wsgi:app
fi
