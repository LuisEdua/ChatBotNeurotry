from pydantic import BaseModel, Field
from typing import List, Optional

class TextDto(BaseModel):
    body: str

class MessageDto(BaseModel):
    from_: str = Field(..., alias='from')
    id: str
    timestamp: str
    text: Optional[TextDto]
    type: str

class ProfileDto(BaseModel):
    name: str

class ContactDto(BaseModel):
    wa_id: str
    profile: ProfileDto

class MetadataDto(BaseModel):
    display_phone_number: str
    phone_number_id: str

class ValueDto(BaseModel):
    messaging_product: str
    metadata: MetadataDto
    contacts: List[ContactDto]
    messages: List[MessageDto]

class ChangeDto(BaseModel):
    field: str
    value: ValueDto

class EntryDto(BaseModel):
    id: str
    changes: List[ChangeDto]

class WhatsAppMessageDto(BaseModel):
    object: str
    entry: List[EntryDto]