from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ApiKey(BaseModel):
    id: Optional[str] = None
    user_id: str
    key: str
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # V2 replacement for orm_mode 