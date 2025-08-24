from pydantic import BaseModel
from bot.cardlink.api_types import Balance


class Balances(BaseModel):
    balances: list[Balance]
