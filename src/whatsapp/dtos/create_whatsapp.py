from pydantic import BaseModel, Field, validator
from typing import List

class Text(BaseModel):
    body: str

class MessageDto(BaseModel):
    id: str
    from_: str = Field(..., alias='from')
    timestamp: str
    text: Text
    type: str

class Value(BaseModel):
    messages: List[MessageDto]

    @validator('messages')
    def messages_must_have_at_least_one_element(cls, v):
        if len(v) < 1:
            raise ValueError('Messages must have at least one element')
        return v

class Change(BaseModel):
    field: str
    value: Value

class Entry(BaseModel):
    id: str
    changes: List[Change]

    @validator('changes')
    def changes_must_have_at_least_one_element(cls, v):
        if len(v) < 1:
            raise ValueError('Changes must have at least one element')
        return v

class WebhookMessageDto(BaseModel):
    object: str
    entry: List[Entry]