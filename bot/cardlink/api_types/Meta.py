from typing import Optional
from pydantic import BaseModel


class Meta(BaseModel):
    path: str
    per_page: int
    prev_cursor: Optional[str] = None
    next_cursor: Optional[str] = None
