from pydantic import BaseModel
from bot.cardlink.api_types import Bank


class Banks(BaseModel):
    data: list[Bank]
