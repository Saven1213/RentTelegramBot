from pydantic import BaseModel
from bot.cardlink.api_types import Payout, Links, Meta


class SearchPayout(BaseModel):
    data: list[Payout]
    links: Links
    meta: Meta
