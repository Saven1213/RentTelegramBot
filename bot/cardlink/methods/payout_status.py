from bot.cardlink.api_types import Payout
from bot.cardlink.error import APIError


async def get_payout_status_method(
        client,
        id: str | None = None,
        order_id: str | None = None
):
    __return_type__ = Payout
    __api_method__ = "payout/status"

    if id is None and order_id is None:
        return APIError(message="Argument not passed")

    data = {}

    if id: data['id'] = id
    if order_id: data['order_id'] = order_id

    return await client.get_request(data=data, return_type=__return_type__, api_method=__api_method__)
