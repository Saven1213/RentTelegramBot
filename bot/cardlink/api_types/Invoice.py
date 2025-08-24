from pydantic import BaseModel
from typing import Literal, Optional


class Invoice(BaseModel):
    id: Optional[str] = None
    bill_id: Optional[str] = None
    order_id: Optional[str] = None
    active: Optional[bool] = None
    status: Optional[Literal["NEW", "PROCESS", "UNDERPAID", "SUCCESS", "OVERPAID", "FAIL"]] = None
    amount: Optional[int] = None
    type: Optional[Literal["MULTI", "NORMAL"]] = None
    created_at: Optional[str] = None
    currency_in: Optional[Literal["USD", "RUB", "EUR"]] = None
    ttl: Optional[int] = None
