import json
import logging
import sys
from typing import Any, Dict, Optional

import requests
from flask import Flask, jsonify, request

# ==================== CONFIGURACIÓN QUEMADA ====================
ACCESS_TOKEN = (
    "EAAT5ytMqWiYBQd6UNFk9a5uLbOZABYgMoomZBATnuZCbzX3pW4ibBPMR6qDDNCESZC8A8tu0bXMkX3ok596EHFb6kkSt6dQVtaXSi1YKZBofEnGMCWnuFDFyxe9YINhmzhi8AnImUNBOORGsPL5Yt0EMI7ggY4ZCwj19gBx4kr5YtoS5UOYwJ02pJgOPfhdon4nHyew4qvkXV3CfqkXVHdLmtGZCt2DKZAab30nl"
)
PHONE_NUMBER_ID = "921658871033993"
API_VERSION = "v24.0"
VERIFY_TOKEN = "1234"  # usado por webhook GET

SUPABASE_URL = "https://fldoqvfhiatsdnoyjmmp.supabase.co"
SUPABASE_SERVICE_ROLE = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZsZG9xdmZoaWF0c2Rub3lqbW1wIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzAxNzcxMywiZXhwIjoyMDcyNTkzNzEzfQ.87QBO4bj0tRPqU6Jm908uBTb2WvXnROgNaHduknSx9k"
)

# Tabla por defecto a leer cuando llega un "1"
DEFAULT_TABLE = "notebooks"

app = Flask(__name__)

# Logging: enviar a stdout para que Render/Gunicorn lo capture
app.logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s"))
if not app.logger.handlers:
    app.logger.addHandler(handler)

# ==================== FUNCIÓN PARA ENVIAR MENSAJE ====================
def send_whatsapp_message(message_body: str, recipient_number: str):
    """
    Envía un mensaje de texto a un número de WhatsApp usando Meta Cloud API
    
    Args:
        message_body (str): El texto del mensaje
        recipient_number (str): Número en formato +XXXXXXXXXXXXX
    
    Returns:
        dict: Respuesta de Meta con el estado del mensaje
    """
    
    # Construir la URL del endpoint
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    
    # Headers requeridos
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Estructura del payload (según Meta oficial 2025/2026)
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_number.replace("+", ""),  # Meta quiere sin el +
        "type": "text",
        "text": {
            "preview_url": False,  # Set True si incluyes URLs
            "body": message_body
        }
    }
    
    try:
        app.logger.info(f"[send_whatsapp_message] to={recipient_number} body={message_body}")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            app.logger.info(f"[send_whatsapp_message] ok id={result.get('messages')[0].get('id')}")
            return result
        else:
            app.logger.error(
                f"[send_whatsapp_message] fail status={response.status_code} resp={response.text}"
            )
            return None
    except Exception as e:
        app.logger.exception(f"[send_whatsapp_message] exception: {e}")
        return None


# ==================== SUPABASE HELPER ====================
def fetch_first_row(table: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una fila (la más reciente) de una tabla de Supabase vía REST.
    Requiere SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
        print("❌ Falta SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")
        return None

    url = f"{SUPABASE_URL}/rest/v1/{table}?order=created_at.desc&limit=1"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data[0] if data else None
        print(f"❌ Error consultando Supabase ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"❌ Error al consultar Supabase: {e}")
    return None


# ==================== WEBHOOK META ====================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Verificación inicial de webhook de Meta.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    Recibe mensajes de WhatsApp. Si el usuario envía "1",
    consulta una fila de Supabase y responde con el JSON.
    """
    body = request.get_json(force=True, silent=True) or {}
    try:
        app.logger.info(f"📥 Webhook payload: {json.dumps(body, ensure_ascii=False)}")
    except Exception as e:
        app.logger.error(f"[receive_message] error logging payload: {e}")
    try:
        # Navegar estructura de Meta
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return jsonify({"status": "no_message"}), 200

        msg = messages[0]
        text = msg.get("text", {}).get("body", "").strip()
        from_number = msg.get("from")

        if text == "1":
            row = fetch_first_row(DEFAULT_TABLE)
            if row:
                send_whatsapp_message(
                    f"Fila de {DEFAULT_TABLE}:\n{json.dumps(row, ensure_ascii=False, indent=2)}",
                    from_number,
                )
            else:
                send_whatsapp_message(
                    f"No encontré datos en {DEFAULT_TABLE} o hubo un error.",
                    from_number,
                )
        else:
            send_whatsapp_message(
                "Envía 1 para recibir una muestra de datos.", from_number
            )
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 200

# ==================== FUNCIÓN AUXILIAR: VALIDAR CREDENCIALES ====================
def validate_credentials():
    """
    Verifica que tengas todas las credenciales necesarias
    """
    if not ACCESS_TOKEN:
        print("❌ ERROR: WHATSAPP_ACCESS_TOKEN no configurado")
        return False
    if not PHONE_NUMBER_ID:
        print("❌ ERROR: WHATSAPP_PHONE_NUMBER_ID no configurado")
        return False
    
    print("✅ Credenciales validadas")
    return True


# ==================== ENDPOINT DE PRUEBA DE ENVÍO ====================
@app.route("/test-send", methods=["GET"])
def test_send():
    """
    Envía un mensaje de prueba al número indicado (query param ?to=).
    Si no se pasa 'to', usa el mismo número que recibimos en el webhook.
    """
    to_number = request.args.get("to", "593961022800").replace("+", "")
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"preview_url": False, "body": "Ping de prueba /test-send"},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        return (
            jsonify(
                {
                    "status": resp.status_code,
                    "response": resp.json() if resp.text else {},
                }
            ),
            resp.status_code,
        )
    except Exception as e:
        app.logger.exception(f"[test_send] exception: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== MAIN ====================
if __name__ == "__main__":
    # Para pruebas locales: flask --app nn run --port 8080
    app.run(host="0.0.0.0", port=8080)
