import datetime
from bot.cardlink.api_types import SearchPayout


async def search_payout_method(
        client,
        start_date: datetime.datetime | None = None,
        finish_date: datetime.datetime | None = None,
        per_page: int | None = None,
        cursor: str | None = None
):
    __return_type__ = SearchPayout
    __api_method__ = "payout/search"

    data = {}

    if start_date: data['start_date'] = start_date
    if finish_date: data['finish_date'] = finish_date
    if per_page: data['per_page'] = per_page
    if cursor: data['cursor'] = cursor

    return await client.get_request(data=data, return_type=__return_type__, api_method=__api_method__)
