import os
import json
import requests
from typing import Optional

BASE_URL = os.getenv("SERVICE_URL", "http://localhost:8080")
RECIPIENT = os.getenv("TEST_RECIPIENT", "593961022800")  # sin +


def check_env():
    required = [
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
        "WHATSAPP_VERIFY_TOKEN",
        "WHATSAPP_API_VERSION",
    ]
    missing = [k for k in required if not os.getenv(k)]
    print(" Env presentes" if not missing else f" Faltan env: {missing}")
    print({k: os.getenv(k) for k in required})
    for k in ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_TABLE"]:
        print(f"{k}={os.getenv(k, '')}")


def ping_webhook():
    url = f"{BASE_URL}/webhook"
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": RECIPIENT, "text": {"body": "1"}}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"POST /webhook -> {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Error POST /webhook: {e}")


def test_send_message():
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    version = os.getenv("WHATSAPP_API_VERSION", "v22.0")
    if not (token and phone_id):
        print("❌ Falta token o phone id")
        return
    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT,
        "type": "text",
        "text": {"body": "Ping desde diagnostic.py"},
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Send message -> {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")


if __name__ == "__main__":
    print("== check_env ==")
    check_env()
    print("== ping_webhook ==")
    ping_webhook()
    print("== test_send_message ==")
    test_send_message()



