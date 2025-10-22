import base64
import hashlib
import hmac
import json
from collections import OrderedDict
from typing import Optional
from urllib.parse import urlencode
import time
import aiohttp
from decimal import Decimal

BASE_URL = 'https://api.btcmarkets.net'

class BTCMarketsAPI:
    _api_key: bytes
    _api_secret: bytes

    def __init__(self, api_key:bytes=None, api_secret:bytes=None) -> None:
        """
        BTCMarkets API client;
        https://docs.btcmarkets.net/
        
        Args:
            api_key (bytes, optional): API key for authenticated requests
            api_secret (bytes, optional): API secret for authenticated requests
        """
        self._api_key = api_key
        self._api_secret = api_secret

    # Public requests here ---- ---- ---- ----
    async def get_active_markets(self) -> dict:
        """ Retrieves list of active markets including configuration for each market. """
        path: str = f'/v3/markets'
        return await self._make_public_http_call(method="GET", path=path)

    async def get_market_orderbook(self, market_id:str) -> dict:
        """ market_id; eg 'BTC-AUD' """
        path: str = f'/v3/markets/{market_id}/orderbook'
        return await self._make_public_http_call(method="GET", path=path)

    # Private requests here ---- ---- ---- ----
    async def get_fee_tier(self) -> dict:
        path = "/v3/accounts/me/trading-fees"
        response = await self._make_private_http_call(method="GET", path=path)
        return response

    async def get_balances(self) -> dict:
        path = "/v3/accounts/me/balances"
        response = await self._make_private_http_call(method="GET", path=path)
        return response

    async def place_new_order(self, market_id:str, price:Decimal, amount:Decimal, order_type:str, side:str) -> dict:
        data = OrderedDict([('marketId', market_id),
                            ('price', f"{price:.8f}"),
                            ('amount', f"{amount:.8f}"),
                            ('type', order_type),
                            ('side', side)])
        path = f'/v3/orders'
        response = await self._make_private_http_call(method="POST", path=path, data=data)
        return response

    async def replace_order(self, price:Decimal, amount:Decimal, order_id:str) -> dict:
        data = OrderedDict([('price', f"{price:.8f}"),
                            ('amount', f"{amount:.8f}")])
        path = f'/v3/orders/{order_id}'
        response = await self._make_private_http_call(method="PUT", path=path, data=data)
        return response

    async def list_orders(self, market_id: Optional[str] = None, status: Optional[str] = None) -> dict:
        params = OrderedDict()
        if market_id: params['market_id'] = market_id
        if status: params['status'] = status
        path = f'/v3/orders'
        response = await self._make_private_http_call(method="GET", path=path, params=params)
        return response

    async def get_order(self, order_id:str) -> dict:
        path = f'/v3/orders/{order_id}'
        response = await self._make_private_http_call(method="GET", path=path)
        return response

    async def cancel_order(self, order_id: Optional[str] = None) -> dict:
        path = f'/v3/orders/{order_id}'
        response = await self._make_private_http_call(method="DELETE", path=path)
        return response

    async def cancel_open_orders(self, market_id: Optional[str] = None) -> dict:
        params = OrderedDict()
        if market_id: params['market_id'] = market_id
        path = f'/v3/orders'
        response = await self._make_private_http_call(method="DELETE", path=path, params=params)
        return response

    # Internal methods
    def _get_secrets(self) -> tuple[bytes, bytes]:
        if None in [self._api_key, self._api_secret]: raise AttributeError("api_key or api_secret not set.")
        return self._api_key, self._api_secret

    async def _make_public_http_call(self, method:str="GET", data:Optional[dict]=None, path:str="") -> dict:
        headers = {
            "Accept":"application/json",
            "Accept-Charset":"UTF-8",
            "Content-Type":"application/json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.request(method=method,
                                    url=BASE_URL + path,
                                    data=data,
                                    headers=headers) as resp:
                result = await resp.json()

                if resp.status == 200:
                    return result
                else:
                    if 'code' in result and 'message' in result:
                        raise ValueError(f"HTTP Response code {resp.status}; {result['code']}-{result['message']}")
                    else:
                        raise ValueError(f"HTTP Response code {resp.status}")

    async def _make_private_http_call(self, method:str="GET", path:str="", params:Optional[dict]=None, data:Optional[dict]=None) -> dict:
        time_in_ms = str(int(time.time() * 1000))  # The time format used by btcmarkets

        if data: post_data = json.dumps(data)
        else: post_data = None

        if params:
            query_string = '?' + urlencode(params)
        else: query_string = ""

        string_to_sign = method + path + time_in_ms
        if post_data: string_to_sign += post_data

        api_key, api_secret = self._get_secrets()
        signature = base64.b64encode(hmac.new(api_secret, string_to_sign.encode('utf-8'), digestmod=hashlib.sha512).digest())
        url = BASE_URL + path + query_string
        headers = {
            "Accept":"application/json",
            "Accept-Charset":"UTF-8",
            "Content-Type":"application/json",
            "BM-AUTH-APIKEY":api_key.decode("utf-8"),
            "BM-AUTH-TIMESTAMP":time_in_ms,
            "BM-AUTH-SIGNATURE":signature.decode('utf8')
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method=method,
                                       url=url,
                                       data=post_data,
                                       headers=headers) as resp:
                result = await resp.json()

                if resp.status == 200:
                    return result
                else:
                    if 'code' in result and 'message' in result:
                        raise ValueError(f"HTTP Response code {resp.status}; {result['code']}-{result['message']}")
                    else:
                        raise ValueError(f"HTTP Response code {resp.status}")

