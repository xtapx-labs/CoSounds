#!/usr/bin/env python3
"""
Raspberry Pi 3 BLE Scanner for CoSounds Presence Detection

This scanner detects Bluetooth devices and reports them to the Django backend.
The Django backend filters for registered devices only.

Usage:
    python3 raspberry-pi-scanner.py

Requirements:
    - Raspberry Pi 3 (has built-in Bluetooth)
    - Python 3.8+
    - pip3 install bleak requests python-dotenv

Setup:
    1. Copy this script to Raspberry Pi
    2. Create .env file with DJANGO_API_URL and SCANNER_API_KEY
    3. Run: python3 raspberry-pi-scanner.py

Author: CoSounds Team
Date: 2025-12-02
"""

import asyncio
import os
import logging
import requests
import time
from datetime import datetime
from bleak import BleakScanner
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment
DJANGO_API_URL = os.getenv('DJANGO_API_URL', 'http://localhost:8000/api')
SCANNER_API_KEY = os.getenv('SCANNER_API_KEY', '')
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', 10))  # 10 seconds
SCAN_TIMEOUT = float(os.getenv('SCAN_TIMEOUT', 5.0))  # 5 seconds
TARGET_MAC = os.getenv('TARGET_MAC_ADDRESS', 'AC:F2:3C:D9:97:4E')  # Target device MAC

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def scan_for_devices():
    """
    Scan for nearby Bluetooth devices using bleak.

    Returns:
        list: Detected devices with MAC, name, and RSSI
    """
    try:
        logger.debug("🔍 Starting BLE scan...")
        devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT)

        detected = []
        for device in devices:
            if device.address:
                detected.append({
                    'device_mac': device.address,
                    'device_name': device.name or 'Unknown Device',
                    'rssi': getattr(device, 'rssi', None)
                })

        logger.info(f"📡 Scan complete: {len(detected)} devices found")
        return detected

    except Exception as e:
        logger.error(f"❌ Scan error: {e}")
        return []


def report_device_to_django(device):
    """
    Report detected device to Django backend.

    Args:
        device: Dict with device_mac, device_name, rssi

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = requests.post(
            f'{DJANGO_API_URL}/scanner/device-detected',
            json={
                'device_mac': device['device_mac'],
                'device_name': device['device_name'],
                'rssi': device['rssi']
            },
            headers={
                'Content-Type': 'application/json',
                'X-Scanner-API-Key': SCANNER_API_KEY
            },
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                action = result.get('action', 'unknown')

                if action == 'restored':
                    logger.info(f"✅ {device['device_mac']}: Restored from grace period")
                elif action == 'connected':
                    logger.info(f"✅ {device['device_mac']}: Reconnected")
                elif action != 'ignored':
                    logger.debug(f"✅ {device['device_mac']}: {action}")

                return True
            else:
                logger.warning(f"⚠️  Django returned success=false for {device['device_mac']}")
                return False
        else:
            logger.error(f"❌ HTTP {response.status_code} for {device['device_mac']}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"⏱️  Timeout reporting {device['device_mac']}")
        return False

    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 Connection error - Cannot reach Django at {DJANGO_API_URL}")
        return False

    except Exception as e:
        logger.error(f"❌ Error reporting {device['device_mac']}: {e}")
        return False


async def scan_and_report_loop():
    """
    Main scanning loop:
    1. Scan for Bluetooth devices
    2. Filter for target MAC address
    3. Report target device to Django if found
    4. Wait for SCAN_INTERVAL seconds
    5. Repeat
    """
    scan_count = 0

    while True:
        try:
            scan_count += 1
            logger.info(f"--- Scan #{scan_count} at {datetime.now().strftime('%H:%M:%S')} ---")

            # Scan for devices
            devices = await scan_for_devices()

            if not devices:
                logger.info("No Bluetooth devices detected in range")
                logger.warning(f"❌ Target device {TARGET_MAC} NOT detected")
            else:
                logger.info(f"📡 Total devices found: {len(devices)}")

                # Filter for target MAC address only
                target_device = None
                for device in devices:
                    if device['device_mac'].upper() == TARGET_MAC.upper():
                        target_device = device
                        break

                if target_device:
                    logger.info(f"🎯 TARGET FOUND: {TARGET_MAC}")
                    if report_device_to_django(target_device):
                        logger.info(f"✅ Successfully reported target device")
                    else:
                        logger.error(f"❌ Failed to report target device")
                else:
                    logger.warning(f"❌ Target device {TARGET_MAC} not in scan results")
                    logger.debug(f"   (Scanned {len(devices)} other devices)")

            # Wait before next scan
            logger.debug(f"⏳ Waiting {SCAN_INTERVAL}s until next scan...")
            await asyncio.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\n🛑 Scanner stopped by user")
            break

        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}")
            logger.info(f"Retrying in {SCAN_INTERVAL}s...")
            await asyncio.sleep(SCAN_INTERVAL)


def verify_configuration():
    """
    Verify required configuration is present.

    Raises:
        ValueError: If configuration is invalid
    """
    if not DJANGO_API_URL:
        raise ValueError("DJANGO_API_URL is not set in .env file")

    if not SCANNER_API_KEY:
        logger.warning("⚠️  SCANNER_API_KEY is not set - API requests may fail")

    logger.info(f"✅ Configuration loaded:")
    logger.info(f"   Django API: {DJANGO_API_URL}")
    logger.info(f"   Target MAC: {TARGET_MAC}")
    logger.info(f"   Scan Interval: {SCAN_INTERVAL} seconds")
    logger.info(f"   Scan Timeout: {SCAN_TIMEOUT} seconds")


async def main():
    """Main entry point for the scanner."""
    print("=" * 60)
    print("🎵 CoSounds BLE Scanner Starting...")
    print("=" * 60)
    print()

    try:
        # Verify configuration
        verify_configuration()
        print()

        # Test Django connection
        logger.info("Testing connection to Django backend...")
        try:
            response = requests.get(f'{DJANGO_API_URL}/health', timeout=5)
            if response.status_code == 200:
                logger.info("✅ Django backend is reachable")
            else:
                logger.warning(f"⚠️  Django returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Cannot reach Django backend: {e}")
            logger.error("Make sure Django is running at the configured URL")
            return

        print()
        logger.info("🚀 Starting scanner loop (press Ctrl+C to stop)")
        logger.info("=" * 60)
        print()

        # Start scanning loop
        await scan_and_report_loop()

    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Please check your .env file")
        return

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return

    finally:
        print()
        logger.info("=" * 60)
        logger.info("👋 Scanner stopped")
        logger.info("=" * 60)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        exit(1)
