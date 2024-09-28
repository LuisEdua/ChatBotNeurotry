import os
import httpx
import json
from typing import Any

async def send_login_fetch(to: str) -> Any:
    url = os.getenv('FACEBOOK_API_URL')
    token = os.getenv('FACEBOOK_API_TOKEN')

    if not url or not token:
        raise ValueError("FACEBOOK_API_URL or FACEBOOK_API_TOKEN environment variables are not set")

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
                "text": "Iniciar sesión",
            },
            "body": {
                "text": "Ingresa tus credenciales para iniciar sesión en tu cuenta.",
            },
            "footer": {
                "text": "Not shown in draft mode",
            },
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_action": "navigate",
                    "flow_token": os.getenv('FLOW_TOKEN'),  # Ensure this is set in your environment
                    "flow_id": os.getenv('LOGIN_FLOW_ID'),  # Ensure this is set in your environment
                    "flow_cta": "Iniciar sesión",
                    "mode": "draft",
                    "flow_action_payload": {
                        "screen": "LOGIN_SCREEN",
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
        response_data = response.json()

        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response_data}")

        return response_data