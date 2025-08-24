from pydantic import BaseModel
from bot.cardlink.api_types import Payment, Links, Meta


class PaymentInvoice(BaseModel):
    data: list[Payment]
    links: Links
    meta: Meta
