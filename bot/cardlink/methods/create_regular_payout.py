from typing import Literal
from bot.cardlink.api_types import Payout


async def create_payout_credit_card_method(
        client,
        amount: float | int,
        currency: Literal['USD', 'RUB', 'EUR'],
        account_identifier: str,
        card_holder: str,
        account_currency: Literal['USD', 'RUB', 'EUR'] = 'RUB',
        recipient_pays_commission: bool | None = None,
        order_id: str | None = None
):
    __return_type__ = Payout
    __api_method__ = "payout/regular/create"

    data = {
        "amount": amount,
        'account_type': 'credit_card',
        'card_holder': card_holder,
        'account_identifier': account_identifier,
        'currency': currency
    }

    if account_currency: data['account_currency'] = account_currency
    if recipient_pays_commission: data['recipient_pays_commission'] = recipient_pays_commission
    if order_id: data['order_id'] = order_id

    return await client.post_request(client=client, data=data, return_type=__return_type__, api_method=__api_method__)


async def create_payout_sbp_method(
        client,
        amount: float | int,
        currency: Literal['USD', 'RUB', 'EUR'],
        account_identifier: str,
        account_bank: str,
        account_currency: Literal['USD', 'RUB', 'EUR'] = 'RUB',
        recipient_pays_commission: bool | None = None,
        order_id: str | None = None
):
    __return_type__ = Payout
    __api_method__ = "payout/regular/create"

    data = {
        "amount": amount,
        'account_type': 'sbp',
        'account_bank': account_bank,
        'account_identifier': account_identifier,
        'currency': currency
    }


    if account_currency: data['account_currency'] = account_currency
    if recipient_pays_commission: data['recipient_pays_commission'] = recipient_pays_commission
    if order_id: data['order_id'] = order_id

    return await client.post_request(client=client, data=data, return_type=__return_type__, api_method=__api_method__)


async def create_payout_crypto_method(
        client,
        amount: float | int,
        currency: Literal['USD', 'RUB', 'EUR'],
        account_identifier: str,
        account_network: Literal['TRX', 'ETH'],
        account_currency: Literal['USD', 'RUB', 'EUR'] = 'RUB',
        recipient_pays_commission: bool | None = None,
        order_id: str | None = None
):
    __return_type__ = Payout
    __api_method__ = "payout/regular/create"

    data = {
        "amount": amount,
        'account_type': 'crypto',
        'account_network': account_network,
        'account_identifier': account_identifier,
        'currency': currency
    }

    if account_currency: data['account_currency'] = account_currency
    if recipient_pays_commission: data['recipient_pays_commission'] = recipient_pays_commission
    if order_id: data['order_id'] = order_id

    return await client.post_request(client=client, data=data, return_type=__return_type__, api_method=__api_method__)


async def create_payout_steam_method(
        client,
        amount: float | int,
        currency: Literal['USD', 'RUB', 'EUR'],
        account_identifier: str,
        account_currency: Literal['USD', 'RUB', 'EUR'] = 'RUB',
        recipient_pays_commission: bool | None = None,
        order_id: str | None = None
):
    __return_type__ = Payout
    __api_method__ = "payout/regular/create"

    data = {
        "amount": amount,
        'account_type': 'steam',
        'account_identifier': account_identifier,
        'currency': currency
    }

    if account_currency: data['account_currency'] = account_currency
    if recipient_pays_commission: data['recipient_pays_commission'] = recipient_pays_commission
    if order_id: data['order_id'] = order_id

    return await client.post_request(data=data, return_type=__return_type__, api_method=__api_method__)

