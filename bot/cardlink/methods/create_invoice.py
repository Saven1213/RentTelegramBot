from typing import Literal
from bot.cardlink.api_types import Item, CreatedInvoice


async def create_invoice_method(
        client,
        amount: float | int,
        order_id: str | None = None,
        description: str | None = None,
        type: Literal['normal', 'multi'] = 'normal',
        currency_in: Literal['RUB', 'USD', 'EUR'] = 'RUB',
        custom: str | None = None,
        payer_pays_commission: Literal[0, 1] = 1,
        payer_email: str = None,
        name: str | None = None,
        ttl: int | None = None,
        success_url: str | None = None,
        fail_url: str | None = None,
        payment_method: Literal["BANK_CARD", "SBP"] = "SBP",
        request_fields_email: bool = False,
        request_fields_phone: bool = False,
        request_fields_name: bool = False,
        request_fields_comment: bool = False,
        items: list[Item] | None = None
    ):
    """
    :param amount: Сумма счета на оплату
    :param order_id: Уникальный идентификатор заказа. Будет возвращен в postback.
    :param description: Описание платежа
    :param type: Тип платежа. Одноразовый или многоразовый. Если выбран одноразовый, то второй раз оплатить не получится.
    :param currency_in: Валюта, в которой оплачивается счет. Если не передана, то используется валюта магазина. Если shop_id не определен, то используется RUB.
    :param custom: Произвольное поле. Будет возвращено в postback.
    :param payer_pays_commission: Параметр, который указывает на то, кто будет оплачивать комиссию за входящий платёж.
    :param payer_email: Параметр, который заполняет email клиента на платёжной странице.
    :param name: Название ссылки. Укажите, за что принимаете средства. Этот текст будет отображен в платежной форме.
    :param ttl: Время жизни счета на оплату в секундах.
    :param success_url: Страница успешной оплаты.
    :param fail_url: Страница неуспешной оплаты.
    :param payment_method: Если указан этот параметр, то при переходе на платежную форму этот способ оплаты будет выбран автоматически, без возможности выбора другого способ оплаты.
    :param request_fields_email: Обязательный запрос электронной почты у плательщика
    :param request_fields_phone: Обязательный запрос номера телефона у плательщика
    :param request_fields_name: Обязательный запрос ФИО у плательщика
    :param request_fields_comment: Обязательный запрос комментария у плательщика
    :param items: Список товаров

    :return: Счёт на оплату
    """

    __api_method__ = "bill/create"
    __return_type__ = CreatedInvoice

    data = {
        "amount": amount,
        "shop_id": client._shop_id,
        "request_fields": {
            "email": request_fields_email,
            "phone": request_fields_phone,
            "name": request_fields_name,
            "comment": request_fields_comment,
        }
    }

    if payment_method: data['payment_method'] = payment_method
    if type: data['type'] = type
    if payer_pays_commission: data['payer_pays_commission']= payer_pays_commission
    if order_id: data["order_id"] = order_id
    if description: data["description"] = description
    if currency_in: data["currency_in"] = currency_in
    if custom: data["custom"] = custom
    if payer_email: data["payer_email"] = payer_email
    if name: data["name"] = name
    if ttl: data["ttl"] = ttl
    if success_url: data["success_url"] = success_url
    if fail_url: data["order_id"] = fail_url
    if items:
        data['items'] = []
        for item in items:
            data['items'].append(
                {
                    "name": item.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "category": item.category,
                    "extra": {
                        "phone": item.extra_phone if item.extra_phone else ''
                    }
                }
            )

    return await client.post_request(data=data, return_type=__return_type__, api_method=__api_method__)


