from bot.cardlink.api_types import Invoice


async def get_payment_status_method(
        client,
        id: str,
        refunds: bool = True,
        chargeback: bool = False
):
    __return_type__ = Invoice
    __api_method__ = "payment/status"

    data = {"id": id, "refunds": refunds, "chargeback": chargeback}

    return await client.get_request(data=data, return_type=__return_type__, api_method=__api_method__)
