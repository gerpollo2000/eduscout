"""
EduScout WhatsApp Tool
YCloud API integration for sending and receiving WhatsApp messages.

YCloud API docs: https://docs.ycloud.com/reference/whatsapp_message-send-directly
"""

import os
import logging
import json
import httpx
from typing import Optional

# Configuramos el logger para que se vea en consola
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YCLOUD_API_BASE = "https://api.ycloud.com/v2"
YCLOUD_API_KEY = os.environ.get("YCLOUD_API_KEY", "").strip()
WHATSAPP_FROM_NUMBER = os.environ.get("WHATSAPP_FROM_NUMBER", "").strip()

def _headers() -> dict:
    return {
        "content-type": "application/json",
        "X-API-Key": YCLOUD_API_KEY,
        "accept": "application/json",
    }


async def send_text_message(to: str, text: str) -> dict:
    # 1. Limpieza rigurosa de números (Igualamos al éxito del CURL)
    # Quitamos espacios y aseguramos el +
    to_clean = to.strip()
    if not to_clean.startswith("+"):
        to_clean = "+" + to_clean
    
    from_clean = WHATSAPP_FROM_NUMBER
    if not from_clean.startswith("+"):
        from_clean = "+" + from_clean

    # 2. Construcción del Payload (Exactamente igual al CURL que te funcionó)
    payload = {
        "from": from_clean,
        "to": to_clean,
        "type": "text",
        "text": {
            "body": text[:4096]
        },
    }

    url = f"{YCLOUD_API_BASE}/whatsapp/messages/sendDirectly"
    headers = _headers()

    # --- BLOQUE DE VERBOSIDAD TOTAL ---
    print("\n" + "="*50)
    print("DEBUG: ENVIANDO PETICIÓN A YCLOUD")
    print(f"URL: {url}")
    print(f"HEADERS: {json.dumps({k: (v if k != 'X-API-Key' else v) for k, v in headers.items()}, indent=2)}")
    print(f"PAYLOAD: {json.dumps(payload, indent=2)}")
    print("="*50 + "\n")
    # ----------------------------------

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

            # Log del resultado
            if response.status_code >= 400:
                logger.error(f"YCloud send failed | Status: {response.status_code}")
                logger.error(f"Response Body: {response.text}")
                return {"error": True, "status": response.status_code, "detail": response.text}

            result = response.json()
            logger.info(f"✅ Message sent successfully! ID: {result.get('id')}")
            return result

        except Exception as e:
            logger.exception(f"Fatal error during request: {e}")
            return {"error": True, "detail": str(e)}

async def send_text_message_sync(to: str, text: str) -> dict:
    """Synchronous wrapper for environments where async isn't available."""
    import asyncio
    return asyncio.run(send_text_message(to, text))


def parse_inbound_message(webhook_payload: dict) -> Optional[dict]:
    """
    Parse a YCloud inbound message webhook payload.

    YCloud webhook event type: whatsapp.inbound_message.received

    Expected payload structure:
    {
        "id": "evt_xxx",
        "type": "whatsapp.inbound_message.received",
        "whatsappInboundMessage": {
            "id": "wamid.xxx",
            "wabaId": "xxx",
            "from": "+14155551234",
            "to": "+1234567890",
            "customerProfile": {
                "name": "John Doe"
            },
            "type": "text",
            "text": {
                "body": "Hello, I need help finding a school"
            },
            "timestamp": "2026-02-18T12:00:00Z"
        }
    }

    Returns:
        Parsed dict with sender, text, name, message_id or None if not a text message
    """
    event_type = webhook_payload.get("type", "")

    if event_type != "whatsapp.inbound_message.received":
        logger.debug(f"Ignoring webhook event type: {event_type}")
        return None

    inbound = webhook_payload.get("whatsappInboundMessage", {})
    msg_type = inbound.get("type", "")

    if msg_type == "text":
        text_body = inbound.get("text", {}).get("body", "")
    elif msg_type == "interactive":
        # Handle button replies
        interactive = inbound.get("interactive", {})
        itype = interactive.get("type", "")
        if itype == "button_reply":
            text_body = interactive.get("buttonReply", {}).get("title", "")
        elif itype == "list_reply":
            text_body = interactive.get("listReply", {}).get("title", "")
        else:
            text_body = str(interactive)
    elif msg_type == "location":
        loc = inbound.get("location", {})
        text_body = f"[Location shared: lat={loc.get('latitude')}, lng={loc.get('longitude')}]"
    else:
        logger.info(f"Unsupported inbound message type: {msg_type}")
        return None

    sender = inbound.get("from", "")
    name = inbound.get("customerProfile", {}).get("name", "Unknown")
    message_id = inbound.get("id", "")

    return {
        "sender": sender,
        "name": name,
        "text": text_body,
        "message_id": message_id,
        "message_type": msg_type,
        "raw": inbound,
    }


async def mark_as_read(message_id: str) -> dict:
    """Mark an inbound message as read (shows blue checkmarks)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{YCLOUD_API_BASE}/whatsapp/inboundMessages/{message_id}/markAsRead",
            headers=_headers(),
        )
        if response.status_code >= 400:
            logger.warning(f"Failed to mark as read: {response.status_code}")
            return {"error": True}
        return response.json() if response.text else {"ok": True}
