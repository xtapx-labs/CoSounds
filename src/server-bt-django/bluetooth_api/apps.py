from django.apps import AppConfig


class BluetoothApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bluetooth_api'

    def ready(self):
        """
        Initialize app when Django starts.
        Start background scheduler for grace period cleanup.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Bluetooth API app is ready")

        # Start scheduler when app is ready
        # Only in main process, not in reloader
        import os
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            try:
                from bluetooth_api.tasks import start_scheduler
                start_scheduler()
                logger.info("Grace period scheduler started")
            except Exception as e:
                logger.error(f"Failed to start scheduler: {e}")
