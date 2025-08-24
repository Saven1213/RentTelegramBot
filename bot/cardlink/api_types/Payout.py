import datetime
from pydantic import BaseModel
from typing import Literal


class Payout(BaseModel):
    id: str | None = None
    status: Literal['NEW', 'MODERATING', 'PROCESS', 'SUCCESS', 'FAIL', 'ERROR', 'DECLINED'] | None = None
    order_id: str | None = None
    account_identifier: str | None = None
    amount: int | float | str | None = None
    account_amount: int | float | str | None = None
    commission: int | float | str | None = None
    account_commission: int | float | str | None = None
    currency: Literal['USD', 'RUB', 'EUR'] | None = None
    account_currency: Literal['USD', 'RUB', 'EUR'] | None = None
    created_at: datetime.datetime | None = None


