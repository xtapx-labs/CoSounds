"""
WSGI config for Bluetooth Presence Detection backend.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Start background scheduler for grace period cleanup
from bluetooth_api.tasks import start_scheduler
start_scheduler()
