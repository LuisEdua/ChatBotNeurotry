import os
import httpx
import json
from typing import Any

async def send_message_fetch(message: str, to: str, preview_url: bool = False) -> Any:
    url = os.getenv('FACEBOOK_API_URL')
    token = os.getenv('FACEBOOK_API_TOKEN')

    if not url or not token:
        raise ValueError("FACEBOOK_API_URL and FACEBOOK_API_TOKEN must be set")

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
    print(body)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=json.dumps(body))
        response_data = response.json()

        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response_data}")

        return response_data