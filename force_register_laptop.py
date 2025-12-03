"""
Force register laptop by inserting directly into Supabase
"""

import requests
import uuid

# Supabase credentials
SUPABASE_URL = "https://bjieozmcptbxgbvzpfyc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJqaWVvem1jcHRieGdidnpwZnljIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjU1NDU3NiwiZXhwIjoyMDc4MTMwNTc2fQ.dlZvMXA82ahKBSelTeDAPwRb2k3PewEyEKIGbrvuCUg"

USER_ID = "00d7e8e1-55c9-4173-b780-5b17de7d820d"
LAPTOP_MAC = "AC:F2:3C:D9:97:4E"
LAPTOP_NAME = "PRANAV"

print("=" * 60)
print("Inserting PRANAV Laptop directly into Supabase")
print("=" * 60)
print()

# Insert device directly
url = f"{SUPABASE_URL}/rest/v1/test_bt_devices"
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

payload = {
    "id": str(uuid.uuid4()),
    "user_id": USER_ID,
    "device_mac": LAPTOP_MAC,
    "device_name": LAPTOP_NAME,
    "status": "disconnected"
}

print(f"Inserting device: {payload}")
print()

response = requests.post(url, headers=headers, json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
print()

if response.status_code in [200, 201]:
    print("✅ SUCCESS! Laptop registered in Supabase")
    print("   Check your Supabase dashboard now!")
else:
    print("❌ ERROR")
    if "duplicate" in response.text.lower() or "unique" in response.text.lower():
        print("   Device already exists (this is OK)")
    else:
        print(f"   {response.text}")

print()
print("=" * 60)
