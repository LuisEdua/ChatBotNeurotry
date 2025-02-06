import os
import httpx
import json
from typing import Any


async def send_catalog_admin_fetch(to: str, data: Any) -> httpx.Response:
    url = os.getenv('FACEBOOK_API_URL')
    token = os.getenv('FACEBOOK_API_TOKEN')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "recipient_type": "individual",
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {
                "type": "text",
                "text": "Publicaciones",
            },
            "body": {
                "text": "Lista de tus publicaciones en Mercado libre.",
            },
            "footer": {
                "text": "Not shown in draft mode",
            },
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_action": "navigate",
                    "flow_token": "<FLOW_TOKEN>",
                    "flow_id": "1705368093531970",
                    "flow_cta": "Ver mis publicaciones",
                    "mode": "published",
                    "flow_action_payload": {
                        "screen": "CATALOG",
                        "data": data
                    },
                },
            },
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=json.dumps(body))
        print(response.json())
        return response