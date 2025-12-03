#!/usr/bin/env python3
"""
Raspberry Pi 3 Classic Bluetooth Scanner for CoSounds Presence Detection
Detects Classic Bluetooth devices (like laptops, phones in discoverable mode)
and reports to Django backend.
"""

import os
import logging
import requests
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
import bluetooth

# Load environment variables
load_dotenv()

# Configuration
DJANGO_API_URL = os.getenv('DJANGO_API_URL', 'http://10.29.148.151:8000/api').rstrip('/')
DEVICE_ENDPOINT = f"{DJANGO_API_URL}/scanner/device-detected"
TARGET_DEVICE_NAME = (os.getenv('TARGET_DEVICE_NAME', '') or '').strip()
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', 10))
SCAN_DURATION = int(os.getenv('SCAN_DURATION', 8))  # Classic BT scan takes longer

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def scan_for_devices():
    """Scan for nearby Classic Bluetooth devices."""
    try:
        logger.debug("Starting Classic Bluetooth scan...")
        
        # Discover nearby Bluetooth devices
        nearby_devices = bluetooth.discover_devices(
            duration=SCAN_DURATION,
            lookup_names=True,
            flush_cache=True,
            lookup_class=False
        )

        detected = []
        for addr, name in nearby_devices:
            detected.append({
                'device_mac': addr,
                'device_name': name or 'Unknown Device',
                'rssi': None  # Classic BT doesn't provide RSSI in basic scan
            })

        return detected
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return []


def report_to_django(device):
    """Report device detection to Django."""
    try:
        payload = {
            'device_mac': device['device_mac'],
            'device_name': device['device_name'],
            'rssi': device['rssi'],
            'seen_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        }

        response = requests.post(
            DEVICE_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json', 'User-Agent': 'cosounds-pi-classic-scanner/1.0'},
            timeout=5,
        )

        if response.status_code == 200:
            result = response.json()
            action = result.get('action', 'unknown')

            if action == 'restored':
                logger.info("   ↳ Device restored from grace period")
            elif action == 'connected':
                logger.info("   ↳ Device reconnected")
            elif action == 'updated':
                logger.info("   ↳ Device last_seen updated")
            else:
                logger.debug(f"   ↳ Action: {action}")

            return True
        else:
            logger.error(f"HTTP {response.status_code}: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot reach Django at {DJANGO_API_URL}")
        return False
    except Exception as e:
        logger.error(f"Error reporting to Django: {e}")
        return False


def scan_loop():
    """Main scanning loop."""
    scan_count = 0

    while True:
        try:
            scan_count += 1
            logger.info(f"=" * 60)
            logger.info(f"Scan #{scan_count} at {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"=" * 60)

            # Scan for devices
            devices = scan_for_devices()

            if not devices:
                logger.warning(f"No Classic Bluetooth devices found")
                logger.info(f"💡 Make sure your devices are in 'discoverable' mode")
            else:
                logger.info(f"✅ Found {len(devices)} Classic Bluetooth devices")
                logger.info("")

                # If TARGET_DEVICE_NAME is empty or "ALL", report all devices
                if not TARGET_DEVICE_NAME or TARGET_DEVICE_NAME.upper() == "ALL":
                    logger.info(f"📡 Reporting ALL {len(devices)} detected devices:")
                    for i, device in enumerate(devices, 1):
                        # Highlight PRANAV laptop and phone
                        mac = device['device_mac'].upper()
                        name = device['device_name']
                        
                        if mac == 'AC:F2:3C:D9:97:4E' or 'PRANAV' in name.upper():
                            logger.info(f"{i}. 🎯 LAPTOP: {mac} ({name})")
                        elif mac == '50:E7:B7:36:79:A4':
                            logger.info(f"{i}. 📱 PHONE: {mac} ({name})")
                        else:
                            logger.info(f"{i}.    {mac} ({name})")
                        
                        report_to_django(device)
                else:
                    # Match by target device name
                    target_found = False
                    for device in devices:
                        device_name = device['device_name'] or ''
                        if TARGET_DEVICE_NAME.upper() in device_name.upper():
                            target_found = True
                            logger.info(f"🎯 TARGET FOUND: {device_name}")
                            logger.info(f"   MAC: {device['device_mac']}")

                            if report_to_django(device):
                                logger.info(f"✅ Reported to Django successfully")
                            else:
                                logger.error(f"❌ Failed to report to Django")
                            break

                    if not target_found:
                        logger.warning(f"❌ Target '{TARGET_DEVICE_NAME}' not in scan results")
                        logger.info(f"💡 Detected devices:")
                        for device in devices:
                            logger.info(f"   - {device['device_mac']}: {device['device_name']}")

            # Wait before next scan
            logger.info("")
            logger.info(f"⏱️  Waiting {SCAN_INTERVAL} seconds before next scan...")
            logger.info("")
            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\nScanner stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(SCAN_INTERVAL)


def main():
    """Main entry point."""
    print()
    print("=" * 60)
    print("CoSounds Classic Bluetooth Scanner")
    print("=" * 60)
    print()

    # Show configuration
    logger.info("Configuration:")
    logger.info(f"   Django API: {DJANGO_API_URL}")
    logger.info(f"   Target Device: {TARGET_DEVICE_NAME or 'ALL'}")
    logger.info(f"   Scan Interval: {SCAN_INTERVAL}s")
    logger.info(f"   Scan Duration: {SCAN_DURATION}s")
    print()

    # Test Django connection
    logger.info("Testing Django connection...")
    try:
        response = requests.get(f"{DJANGO_API_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Django backend is reachable")
        else:
            logger.warning(f"⚠️  Django returned status {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Cannot reach Django: {e}")
        logger.error("Make sure Django is running at {DJANGO_API_URL}")
        return

    print()
    logger.info("🔍 Starting Classic Bluetooth scanner...")
    logger.info("💡 Target devices:")
    logger.info("   🎯 Laptop PRANAV: AC:F2:3C:D9:97:4E")
    logger.info("   📱 Phone: 50:E7:B7:36:79:A4")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    print()

    # Start scanning
    scan_loop()

    print()
    logger.info("=" * 60)
    logger.info("Scanner stopped")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)
