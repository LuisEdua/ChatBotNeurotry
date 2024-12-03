from pydantic import BaseModel

class RegisterResponse(BaseModel):
    name: str
    email: str
    password: str
    tos_optin: bool
    flow_token: str
