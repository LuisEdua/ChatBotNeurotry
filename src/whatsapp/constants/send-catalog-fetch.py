import os
import httpx
import json
from typing import Any


async def send_catalog_fetch(to: str, data: Any) -> httpx.Response:
    url = os.getenv('FACEBOOK_API_URL')
    token = os.getenv('FACEBOOK_API_TOKEN')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    body = {
        "recipient_type": "individual",
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {
                "type": "text",
                "text": "¡Bienvenido a la tienda!"
            },
            "body": {
                "text": "Haz click en el botón para ver nuestro catálogo",
            },
            "action": {
                "name": "flow",
                "parameters": {
                    "mode": "published",
                    "flow_message_version": "3",
                    "flow_token": "AQAAAAACS5FpgQ_cAAAAAD0QI3s.",
                    "flow_id": "1705368093531970",
                    "flow_cta": "Ver catálogo",
                    "flow_action": "navigate",
                    "flow_action_payload": {
                        "screen": "CATALOG",
                        "data": data
                    }
                }
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=json.dumps(body))
        return response