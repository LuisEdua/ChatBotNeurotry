import os
import httpx
import json
from typing import Any

async def send_login_fetch(to: str) -> Any:
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
                    "flow_token": "<FLOW_TOKEN>",
                    "flow_id": "YOUR_LOGIN_FLOW_ID",  # Reemplaza con tu flow ID específico
                    "flow_cta": "Iniciar sesión",
                    "mode": "draft",
                    "flow_action_payload": {
                        "screen": "LOGIN_SCREEN",  # Pantalla de inicio de sesión
                        "data": {
                            "customvalue": "<CUSTOM_VALUE>",  # Reemplaza con valores personalizados si es necesario
                        },
                    },
                },
            },
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=json.dumps(body))
        return response.json()
