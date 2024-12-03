from pydantic import BaseModel, Field
from typing import List

class Pricing(BaseModel):
    billable: bool
    pricing_model: str
    category: str

class Origin(BaseModel):
    type: str

class Conversation(BaseModel):
    id: str
    origin: Origin

class Status(BaseModel):
    id: str
    status: str
    timestamp: str
    recipient_id: str
    conversation: Conversation
    pricing: Pricing

class Metadata(BaseModel):
    display_phone_number: str
    phone_number_id: str

class Value(BaseModel):
    messaging_product: str
    metadata: Metadata
    statuses: List[Status]

class Change(BaseModel):
    value: Value
    field: str

class Entry(BaseModel):
    id: str
    changes: List[Change]

class MessageStatus(BaseModel):
    object: str
    entry: List[Entry]