from pydantic import BaseModel
from typing import Literal, Any


class Payment(BaseModel):
    id: str
    bill_id: str
    status: Literal["NEW", "PROCESS", "UNDERPAID", "SUCCESS", "OVERPAID", "FAIL"]
    amount: int | float
    commission: int | float
    account_amount: int | float
    account_currency_code: Literal["USD", "RUB", "EUR"]
    refunded_amount: Any
    from_card: str
    currency_in: Literal["USD", "RUB", "EUR"]
    created_at: str
