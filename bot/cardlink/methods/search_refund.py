import datetime
from bot.cardlink.api_types import SearchRefund


async def search_refund(
        client,
        payment_id: str | None = None,
        start_date: datetime.datetime | None = None,
        finish_date: datetime.datetime | None = None,
        shop_id: str | None = None,
        per_page: int | None = None,
        cursor: str | None = None,
):
    __return_type__ = SearchRefund
    __api_method__ = "refund/search"

    data = {}

    if payment_id: data['payment_id'] = str(payment_id)
    if start_date: data['start_date'] = str(start_date)
    if finish_date: data['finish_date'] = str(finish_date)
    if shop_id: data['shop_id'] = shop_id
    if per_page: data['per_page'] = per_page
    if cursor: data['cursor'] = cursor

    return await client.get_request(data=data, return_type=__return_type__, api_method=__api_method__)
