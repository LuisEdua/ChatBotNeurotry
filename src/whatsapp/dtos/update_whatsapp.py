from typing import Optional, List
from src.whatsapp.dtos.create_whatsapp import WebhookMessageDto, Entry

class UpdateWhatsappDto(WebhookMessageDto):
    object: Optional[str]
    entry: Optional[List[Entry]]