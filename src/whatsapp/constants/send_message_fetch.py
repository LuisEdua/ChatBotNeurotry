import os
import httpx
import json
from typing import Any

async def send_message_fetch(to: str, message: str, preview_url: bool = False) -> Any:
    url = os.getenv('FACEBOOK_API_URL')
    token = os.getenv('FACEBOOK_API_TOKEN')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    body = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": preview_url,
            "body": message,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=json.dumps(body))
        return response.json()