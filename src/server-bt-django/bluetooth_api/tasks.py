"""
Background tasks for Bluetooth Presence Detection.
Grace period cleanup runs every 30 seconds via APScheduler.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()
scheduler_started = False


def cleanup_grace_periods_task():
    """
    Background task that runs every 30 seconds.
    Checks for:
    1. Devices that haven't been detected for 30s → start grace period
    2. Devices with expired grace periods (15 min) → end session
    """
    try:
        from .services import get_supabase_service
        service = get_supabase_service()
        service.cleanup_expired_grace_periods()
        logger.debug("Grace period cleanup completed")

    except Exception as e:
        logger.error(f"Error in grace period cleanup task: {e}")


def start_scheduler():
    """
    Start the APScheduler background scheduler.
    Called when Django app is ready.
    """
    global scheduler_started

    if scheduler_started:
        logger.info("Scheduler already started")
        return

    try:
        # Add grace period cleanup job
        scheduler.add_job(
            cleanup_grace_periods_task,
            trigger=IntervalTrigger(seconds=settings.DETECTION_TIMEOUT_SECONDS),
            id='grace_period_cleanup',
            name='Cleanup expired grace periods',
            replace_existing=True
        )

        # Start scheduler
        scheduler.start()
        scheduler_started = True

        logger.info(f"Background scheduler started (runs every {settings.DETECTION_TIMEOUT_SECONDS}s)")

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise


def stop_scheduler():
    """
    Stop the background scheduler.
    Called when Django app shuts down.
    """
    global scheduler_started

    if scheduler_started:
        scheduler.shutdown()
        scheduler_started = False
        logger.info("Background scheduler stopped")
