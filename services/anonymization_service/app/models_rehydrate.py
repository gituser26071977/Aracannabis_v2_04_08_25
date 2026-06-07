from pydantic import BaseModel

class RehydrateRequest(BaseModel):
    consultation_id: int
    text: str

class RehydrateResponse(BaseModel):
    original_text: str
    status: str
