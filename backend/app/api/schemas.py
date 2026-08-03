from pydantic import BaseModel
from typing import Optional

class TravelCardBase(BaseModel):
    type: str
    title: str
    content: Optional[str] = "{}"

class TravelCardCreate(TravelCardBase):
    pass

class TravelCardOut(TravelCardBase):
    id: str
    class Config:
        from_attributes = True
