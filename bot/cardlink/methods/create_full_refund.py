from bot.cardlink.api_types import Refund


async def create_full_refund_method(
        client,
        payment_id: str
    ):
    """
    :param client: CardLink класс
    :param payment_id: Уникальный идентификатор платежа
    :return: Refund класс
    """

    __api_method__ = "refund/full/create"
    __return_type__ = Refund

    data = {
        "payment_id": payment_id
    }

    return await client.post_request(data=data, return_type=__return_type__, api_method=__api_method__)
