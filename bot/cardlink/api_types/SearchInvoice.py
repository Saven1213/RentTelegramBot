from pydantic import BaseModel
from bot.cardlink.api_types import Invoice, Links, Meta


class SearchInvoice(BaseModel):
    data: list[Invoice]
    links: Links
    meta: Meta
