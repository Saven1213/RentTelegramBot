from bot.cardlink.api_types import Refund


async def create_partial_refund_method(
        client,
        payment_id: str,
        amount: int | float
    ):
    __api_method__ = "refund/partial/create"
    __return_type__ = Refund

    data = {
        "payment_id": payment_id,
        "amount": amount
    }

    return await client.post_request(data=data, return_type=__return_type__, api_method=__api_method__)


