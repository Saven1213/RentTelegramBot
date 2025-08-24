from bot.cardlink.api_types import Banks


async def get_sbp_banks(
        client,
):
    __return_type__ = Banks
    __api_method__ = "payout/dictionaries/sbp_banks"

    return await client.get_request(data={}, return_type=__return_type__, api_method=__api_method__)
