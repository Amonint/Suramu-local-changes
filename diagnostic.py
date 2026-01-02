import json
import requests

BASE_URL = "https://liv-chatbot.onrender.com"
RECIPIENT = "593961022800"  # sin +

WHATSAPP_ACCESS_TOKEN = (
    "EAAT5ytMqWiYBQd6UNFk9a5uLbOZABYgMoomZBATnuZCbzX3pW4ibBPMR6qDDNCESZC8A8tu0bXMkX3ok596EHFb6kkSt6dQVtaXSi1YKZBofEnGMCWnuFDFyxe9YINhmzhi8AnImUNBOORGsPL5Yt0EMI7ggY4ZCwj19gBx4kr5YtoS5UOYwJ02pJgOPfhdon4nHyew4qvkXV3CfqkXVHdLmtGZCt2DKZAab30nl"
)
WHATSAPP_PHONE_NUMBER_ID = "921658871033993"
WHATSAPP_API_VERSION = "v24.0"


def check_env():
    print("Valores quemados:")
    print(
        {
            "WHATSAPP_ACCESS_TOKEN": "***",
            "WHATSAPP_PHONE_NUMBER_ID": WHATSAPP_PHONE_NUMBER_ID,
            "WHATSAPP_API_VERSION": WHATSAPP_API_VERSION,
            "BASE_URL": BASE_URL,
            "RECIPIENT": RECIPIENT,
        }
    )


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
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
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



