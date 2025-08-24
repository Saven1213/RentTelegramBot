from bot.cardlink.api_types import Invoice


async def get_status(
        client,
        id: str
):
    __return_type__ = Invoice
    __api_method__ = "refund/status"

    data = {"id": id}

    return await client.get_request(data=data, return_type=__return_type__, api_method=__api_method__)
