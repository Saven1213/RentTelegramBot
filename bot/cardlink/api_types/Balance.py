from pydantic import BaseModel


class Balance(BaseModel):
    currency: str
    balance_available: str
    balance_locked: str
    balance_hold: str
