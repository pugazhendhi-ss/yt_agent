from pydantic import BaseModel

class ChatPayload(BaseModel):
    id: str
    query: str


