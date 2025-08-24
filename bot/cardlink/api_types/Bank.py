from pydantic import BaseModel


class Bank(BaseModel):
    member_id: int
    name: str
    name_en: str
    bic: int
