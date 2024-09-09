from pydantic import BaseModel, Field

class Context(BaseModel):
    from_: str = Field(..., alias='from')
    id: str

class NfmReply(BaseModel):
    response_json: str
    body: str
    name: str

class Interactive(BaseModel):
    type: str
    nfm_reply: NfmReply

class InteractiveMessage(BaseModel):
    context: Context
    from_: str = Field(..., alias='from')
    id: str
    timestamp: str
    type: str
    interactive: Interactive