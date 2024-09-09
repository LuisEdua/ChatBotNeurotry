import os
import httpx
import json
from typing import Any

async def send_registration_fetch(to: str) -> Any:
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
                "text": "Registrate",
            },
            "body": {
                "text": "Continua y registrate para poder acceder a nuestros productos y servicios",
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
                    "flow_id": "893715122572700",
                    "flow_cta": "Continuar",
                    "mode": "draft",
                    "flow_action_payload": {
                        "screen": "JOIN_NOW",
                        "data": {
                            "customvalue": "<CUSTOM_VALUE>",
                        },
                    },
                },
            },
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=json.dumps(body))
        return response.json()