from pydantic import BaseModel
from bot.cardlink.api_types import Links, Meta
from bot.cardlink.api_types import Refund


class SearchRefund(BaseModel):
    data: list[Refund]
    links: Links
    meta: Meta
