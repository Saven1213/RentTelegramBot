import ssl
from urllib.parse import urlencode
import certifi
from aiohttp import TCPConnector
from aiohttp import ClientSession
import loggers
from api.base import BaseSession
from error import APIError
from methods.create_full_refund import create_full_refund_method
from methods.create_invoice import create_invoice_method
from methods.create_partial_refund import create_partial_refund_method
from methods.create_personal_payout import create_personal_payout_method
from methods.create_regular_payout import create_payout_credit_card_method, create_payout_sbp_method, create_payout_crypto_method, create_payout_steam_method
from methods.get_balance import get_balance_method
from methods.invoice_status import get_invoice_status_method
from methods.payment_status import get_payment_status_method
from methods.payout_status import get_payout_status_method
from methods.search_invoice import search_invoice_method
from methods.search_payments import search_payments_method
from methods.search_payout import search_payout_method
from methods.toggle_activity import toggle_activity_method
from methods.token_valid import token_valid


class CardLink(BaseSession):
    def __init__(self, token: str, shop_id: str):
        self._token = token
        self._shop_id = shop_id
        self._session: ClientSession | None = None
        self.__auth()


    def __auth(self):
        result_auth = token_valid(token=self._token)
        if not result_auth:
            raise APIError("Authorization failed", 401)
        loggers.logger.info("Successful authorization in CardLink API")


    async def post_request(self, data, return_type, api_method):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self._session = ClientSession(
            connector=TCPConnector(
                ssl_context=ssl_context,
            ),
        )
        try:
            async with self._session.post(
                url=f"https://cardlink.link/api/v1/{api_method}",
                json=data,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json"
                },
            ) as resp:
                response = self._check_response(return_type, resp.status, await resp.json(), api_method)
            return response
        finally:
            await self._session.close()
    async def get_request(self, data, return_type, api_method):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self._session = ClientSession(
            connector=TCPConnector(
                ssl_context=ssl_context,
            ),
        )
        try:
            async with self._session.get(
                url=f"https://cardlink.link/api/v1/{api_method}?{urlencode(data)}",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json"
                },
            ) as resp:
                response = self._check_response(return_type, resp.status, await resp.json(), api_method)
            return response
        finally:
            await self._session.close()

    def _check_response(self, return_type, code, data, api_method):
        if data.get('success') or data.get('success') == 'true':
            data.pop('success')

            if (
                    'data' in data and
                    api_method in [
                        'payout/dictionaries/sbp_banks',
                        'payout/personal/create',
                        'payout/regular/create'
                    ]
            ):
                data = data['data']
            print(data)
            return return_type(**data)
        raise APIError(message=data.get('message'), code=code)

    async def create_invoice(self, *args, **kwargs):
        return await create_invoice_method(self, *args, **kwargs)
    async def create_full_refund(self, *args, **kwargs):
        return await create_full_refund_method(self, *args, **kwargs)
    async def create_partial_refund(self, *args, **kwargs):
        return await create_partial_refund_method(self, *args, **kwargs)
    async def create_personal_payout(self, *args, **kwargs):
        return await create_personal_payout_method(self, *args, **kwargs)
    async def create_payout_credit_card(self, *args, **kwargs):
        return await create_payout_credit_card_method(self, *args, **kwargs)
    async def create_payout_steam(self, *args, **kwargs):
        return await create_payout_steam_method(self, *args, **kwargs)
    async def create_payout_crypto(self, *args, **kwargs):
        return await create_payout_crypto_method(self, *args, **kwargs)
    async def create_payout_sbp(self, *args, **kwargs):
        return await create_payout_sbp_method(self, *args, **kwargs)
    async def get_balance(self):
        return await get_balance_method(self)
    async def get_invoice_status(self, *args, **kwargs):
        return await get_invoice_status_method(self, *args, **kwargs)
    async def toggle_activity(self, *args, **kwargs):
        return await toggle_activity_method(self, *args, **kwargs)
    async def get_payout_status(self, *args, **kwargs):
        return await get_payout_status_method(self, *args, **kwargs)
    async def search_invoice(self, *args, **kwargs):
        return await search_invoice_method(self, *args, **kwargs)
    async def search_payments(self, *args, **kwargs):
        return await search_payments_method(self, *args, **kwargs)
    async def search_payout(self, *args, **kwargs):
        return await search_payout_method(self, *args, **kwargs)
    async def get_payment_status(self, *args, **kwargs):
        return await get_payment_status_method(self, *args, **kwargs)



