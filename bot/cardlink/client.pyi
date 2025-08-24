import datetime
from typing import Optional, Literal
from aiohttp import ClientSession
from bot.cardlink.api_types import Balances, PaymentsInvoice
from bot.cardlink.api_types import Refund, SearchPayout, SearchInvoice, Invoice
from bot.cardlink.api_types.Payout import Payout
from bot.cardlink.error import APIError


class CardLink:
    _token: str
    _shop_id: str
    _session: Optional[ClientSession]

    def __init__(self, token: str, shop_id: str) -> None: ...
    def __auth(self) -> None | APIError: ...
    async def create_invoice(
        self,
        amount: float | int,
        order_id: Optional[str] = ...,
        description: Optional[str] = ...,
        type: Literal['normal', 'multi'] = ...,
        currency_in: Literal['RUB', 'USD', 'EUR'] = ...,
        custom: Optional[str] = ...,
        payer_pays_commission: Literal[0, 1] = ...,
        payer_email: Optional[str] = ...,
        name: Optional[str] = ...,
        ttl: Optional[int] = ...,
        success_url: Optional[str] = ...,
        fail_url: Optional[str] = ...,
        payment_method: Literal["BANK_CARD", "SBP"] = ...,
        request_fields_email: bool = ...,
        request_fields_phone: bool = ...,
        request_fields_name: bool = ...,
        request_fields_comment: bool = ...,
        items: Optional[list] = ...,
    ) -> Invoice | APIError: ...
    async def create_full_refund(
        self,
        payment_id: str = ...
    ) -> Refund | APIError: ...
    async def create_partial_refund(
        self,
        payment_id: str = ...,
        amount: int | float = ...,
    ) -> Refund | APIError: ...
    async def create_personal_payout(
        self,
        amount: float | int,
        payout_account_id: str,
        account_currency: Optional[Literal['USD', 'RUB', 'EUR']] = ...,
        recipient_pays_commission: Optional[bool] = ...,
        order_id: Optional[str] = ...,
    ) -> Payout | APIError: ...
    async def create_payout_credit_card(
        self,
        amount: float | int,
        currency: Literal['USD', 'RUB', 'EUR'],
        account_identifier: str,
        card_holder: str,
        account_currency: Literal['USD', 'RUB', 'EUR'] = ...,
        recipient_pays_commission: Optional[bool] = ...,
        order_id: Optional[str] = ...,
    ) -> Payout | APIError: ...
    async def create_payout_sbp(
        self,
        amount: float | int,
        currency: Literal['USD', 'RUB', 'EUR'],
        account_identifier: str,
        account_bank: str,
        account_currency: Literal['USD', 'RUB', 'EUR'] = ...,
        recipient_pays_commission: Optional[bool] = ...,
        order_id: Optional[str] = ...,
    ) -> Payout | APIError: ...
    async def create_payout_crypto(
        self,
        amount: float | int,
        currency: Literal['USD', 'RUB', 'EUR'],
        account_identifier: str,
        account_network: Literal['TRX', 'ETH'],
        account_currency: Literal['USD', 'RUB', 'EUR'] = ...,
        recipient_pays_commission: Optional[bool] = ...,
        order_id: Optional[str] = ...,
    ) -> Payout | APIError: ...
    async def create_payout_steam(
        self,
        amount: float | int,
        currency: Literal['USD', 'RUB', 'EUR'],
        account_identifier: str,
        account_currency: Literal['USD', 'RUB', 'EUR'] = ...,
        recipient_pays_commission: Optional[bool] = ...,
        order_id: Optional[str] = ...,
    ) -> Payout | APIError: ...
    async def get_balance(self) -> Balances | APIError: ...
    async def get_invoice_status(
        self,
        id: str,
    ) -> Invoice | APIError: ...
    async def toggle_activity(
        self,
        id: str,
        per_page: Optional[int] = ...,
        cursor: Optional[str] = ...,
    ) -> SearchInvoice | APIError: ...
    async def get_payout_status(
        self,
        id: Optional[str] = ...,
        order_id: Optional[str] = ...,
    ) -> Payout | APIError: ...
    async def search_invoice(
        self,
        start_date: Optional[datetime.datetime] = ...,
        finish_date: Optional[datetime.datetime] = ...,
        shop_id: Optional[str] = ...,
        per_page: Optional[int] = ...,
        cursor: Optional[str] = ...,
    ) -> SearchInvoice: ...
    async def search_payments(
        self,
        start_date: Optional[datetime.datetime] = ...,
        finish_date: Optional[datetime.datetime] = ...,
        shop_id: Optional[str] = ...,
        per_page: Optional[int] = ...,
        cursor: Optional[str] = ...,
    ) -> PaymentsInvoice: ...
    async def search_payout(
        self,
        start_date: Optional[datetime.datetime] = ...,
        finish_date: Optional[datetime.datetime] = ...,
        per_page: Optional[int] = ...,
        cursor: Optional[str] = ...,
    ) -> SearchPayout: ...
    async def get_payment_status(
        self,
        id: str = ...,
        refunds: bool = ...,
        chargeback: bool = ...,
    ) -> Invoice: ...
