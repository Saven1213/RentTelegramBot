from bot.cardlink.api_types import SearchInvoice


async def toggle_activity_method(
        client,
        id: str,
        per_page: int = None,
        cursor: str = None,
):
    __return_type__ = SearchInvoice
    __api_method__ = "bill/payments"

    data = {"id": id}

    if per_page: data['per_page'] = per_page
    if cursor: data['cursor'] = cursor

    return await client.get_request(data=data, return_type=__return_type__, api_method=__api_method__)
