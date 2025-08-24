from typing import Optional
from pydantic import BaseModel


class Links(BaseModel):
    prev: Optional[str] = None
    next: Optional[str] = None
