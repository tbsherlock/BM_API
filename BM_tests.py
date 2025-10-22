import unittest
from decimal import Decimal
from unittest.mock import patch
from src.BM_api import BTCMarketsAPI


class TestBTCMarketsAPI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bm_api = BTCMarketsAPI()

    async def test_get_active_markets(self):
        response = await self.bm_api.get_active_markets()
        print(f"get_active_markets: {response}")

    async def test_get_market_orderbook(self):
        response = await self.bm_api.get_market_orderbook("BTC-AUD")
        print(f"get_market_orderbook: {response}")

    async def test_place_order(self):
        # Show how to use api key and secret
        api_key: bytes = b'4229ee2d-6b83-477e-a1ab-502dd1f5052c'
        api_secret: bytes = b'anVzdCBhIHRlc3QsIG5vIHNlY3JldHMgaGVyZQ=='
        self.bm_api = BTCMarketsAPI(api_key=api_key, api_secret=api_secret)

        call_response = {'orderId':'11223344556', 'marketId':'BTC-AUD', 'side':'Ask', 'type':'Limit',
         'creationTime':'2025-10-10T01:01:01.200000Z', 'price':'100000', 'amount':'0.1', 'openAmount':'0.1',
         'status':'Accepted'}
        with patch.object(self.bm_api, '_make_private_http_call', return_value=call_response):
            response = await self.bm_api.place_new_order(market_id="BTC-AUD",
                                              price=Decimal(100000),
                                              amount=Decimal(0.1),
                                              order_type="Limit",
                                              side="Ask")

        print(f"test_place_order: {response}")


if __name__ == '__main__':
    unittest.main()
