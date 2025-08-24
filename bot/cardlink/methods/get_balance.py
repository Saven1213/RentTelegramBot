from bot.cardlink.api_types import Balances


async def get_balance_method(
        client,
):
    __return_type__ = Balances
    __api_method__ = "merchant/balance"

    return await client.get_request(data={}, return_type=__return_type__, api_method=__api_method__)
