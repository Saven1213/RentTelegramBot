import datetime
from bot.cardlink.api_types import SearchInvoice


async def search_invoice_method(
        client,
        start_date: datetime.datetime | None = None,
        finish_date: datetime.datetime | None = None,
        shop_id: str | None = None,
        per_page: int | None = None,
        cursor: str | None = None,
):
    __return_type__ = SearchInvoice
    __api_method__ = "bill/search"

    data = {}

    if start_date: data['start_date'] = str(start_date)
    if finish_date: data['finish_date'] = str(finish_date)
    if shop_id: data['shop_id'] = shop_id
    if per_page: data['per_page'] = per_page
    if cursor: data['cursor'] = cursor

    return await client.get_request(data=data, return_type=__return_type__, api_method=__api_method__)
