import datetime
from pydantic import BaseModel
from typing import Literal


class Refund(BaseModel):
    id: str | None = None
    status: Literal["NEW", "PROCESS", "SUCCESS", "FAIL"] | None = None
    amount: int | float | None = None
    currency_in: Literal["USD", "RUB", "EUR"] | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: datetime.datetime | None = None

