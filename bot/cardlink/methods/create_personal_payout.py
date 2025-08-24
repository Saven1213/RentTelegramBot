from typing import Literal
from bot.cardlink.api_types import Payout


async def create_personal_payout_method(
        client,
        amount: float | int,
        payout_account_id: str,
        account_currency: Literal['USD', 'RUB', 'EUR'] | None = None,
        recipient_pays_commission: bool | None = None,
        order_id: str | None = None
):
    __return_type__ = Payout
    __api_method__ = "payout/personal/create"

    data = {"amount": amount, 'payout_account_id': payout_account_id}
    if account_currency: data['account_currency'] = account_currency
    if recipient_pays_commission: data['recipient_pays_commission'] = recipient_pays_commission
    if order_id: data['order_id'] = order_id

    return await client.post_request(data=data, return_type=__return_type__, api_method=__api_method__)
