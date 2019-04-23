import json
import os

import pytest
import requests_mock
from urllib.parse import urlencode

from binance_chain.http import HttpApiClient, AsyncHttpApiClient
from binance_chain.constants import PeerType, OrderSide, OrderType, TransactionSide, TransactionType, KlineInterval
from binance_chain.environment import BinanceEnvironment


class TestClient:

    @pytest.fixture
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture
    def httpclient(self, env):
        return HttpApiClient(env=env, requests_params={'timeout': 1})

    def load_fixture(self, file_name):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        with open(f'{this_dir}/fixtures/{file_name}', 'r') as f:
            return json.load(f)

    def test_get_time(self, httpclient):
        assert httpclient.get_time()

    def test_get_node_info(self, httpclient):
        assert httpclient.get_node_info()

    def test_get_validators(self, httpclient):
        assert httpclient.get_validators()

    def test_get_peers(self, httpclient):
        assert httpclient.get_peers()

    def test_get_transaction(self, httpclient):
        assert httpclient.get_transaction('B17DB550FCE00268C07D11F312E86F72813481124831B798FDC491E363D17989')

    @pytest.mark.parametrize("peer_type", [
        PeerType.NODE,
        PeerType.WEBSOCKET
    ])
    def test_get_peers_capability_node(self, peer_type, httpclient):
        with requests_mock.mock() as m:
            m.get(httpclient._create_uri('peers'), json=self.load_fixture('peers.json'))
            peers = httpclient.get_peers(peer_type=peer_type)
            for p in peers:
                assert peer_type in p['capabilities']

    def test_get_node_peers(self, httpclient):
        with requests_mock.mock() as m:
            m.get(httpclient._create_uri('peers'), json=self.load_fixture('peers.json'))
            peers = httpclient.get_node_peers()
            for p in peers:
                assert PeerType.NODE in p['capabilities']
            assert httpclient.get_peers()

    def test_get_websocket_peers(self, httpclient):
        with requests_mock.mock() as m:
            m.get(httpclient._create_uri('peers'), json=self.load_fixture('peers.json'))
            peers = httpclient.get_websocket_peers()
            for p in peers:
                assert PeerType.WEBSOCKET in p['capabilities']
            assert httpclient.get_peers()

    def test_get_tokens(self, httpclient):
        assert httpclient.get_tokens()

    def test_get_markets(self, httpclient):
        assert httpclient.get_markets()

    def test_get_fees(self, httpclient):
        assert httpclient.get_fees()

    def test_get_trades_url(self, httpclient):
        params = {
            'symbol': 'BNB',
            'side': OrderSide.BUY.value,
            'quoteAsset': 'B.BTC',
            'buyerOrderId': 'buyer_id',
            'sellerOrderId': 'seller_id',
            'height': 3000,
            'offset': 1,
            'limit': 100,
            'start': 2000,
            'end': 5000,
            'total': 5
        }
        qs = urlencode(params)
        with requests_mock.mock() as m:
            m.get(httpclient._create_uri('trades') + '?' + qs, json=self.load_fixture('success.json'))
            res = httpclient.get_trades(
                symbol='BNB',
                side=OrderSide.BUY,
                quote_asset='B.BTC',
                buyer_order_id='buyer_id',
                seller_order_id='seller_id',
                height='3000',
                offset=1,
                limit=100,
                start_time=2000,
                end_time=5000,
                total=5
            )
            assert res == {"message": "success"}

    def test_get_transactions_url(self, httpclient):
        addr = 'tbnb2jadf8u2'
        params = {
            'address': addr,
            'symbol': 'BNB',
            'side': TransactionSide.RECEIVE.value,
            'txAsset': 'B.BTC',
            'txType': TransactionType.BURN_TOKEN.value,
            'blockHeight': 3000,
            'offset': 1,
            'limit': 100,
            'startTime': 2000,
            'endTime': 5000
        }
        qs = urlencode(params)
        with requests_mock.mock() as m:
            m.get(httpclient._create_uri('transactions') + '?' + qs, json=self.load_fixture('success.json'))
            res = httpclient.get_transactions(
                address=addr,
                symbol='BNB',
                side=TransactionSide.RECEIVE,
                tx_asset='B.BTC',
                tx_type=TransactionType.BURN_TOKEN,
                height='3000',
                offset=1,
                limit=100,
                start_time=2000,
                end_time=5000
            )
            assert res == {"message": "success"}

    def test_get_klines_url(self, httpclient):
        params = {
            'symbol': 'BNB',
            'interval': KlineInterval.ONE_DAY.value,
            'limit': 100,
            'startTime': 2000,
            'endTime': 5000
        }
        qs = urlencode(params)
        with requests_mock.mock() as m:
            m.get(httpclient._create_uri('klines') + '?' + qs, json=self.load_fixture('success.json'))
            res = httpclient.get_klines(
                symbol='BNB',
                interval=KlineInterval.ONE_DAY,
                limit=100,
                start_time=2000,
                end_time=5000
            )
            assert res == {"message": "success"}


class TestAsyncClient:

    @pytest.fixture
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture
    @pytest.mark.asyncio
    async def httpclient(self, env, event_loop):
        return await AsyncHttpApiClient.create(loop=event_loop, env=env, requests_params={'timeout': 1})

    def load_fixture(self, file_name):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        with open(f'{this_dir}/fixtures/{file_name}', 'r') as f:
            return json.load(f)

    @pytest.mark.asyncio
    async def test_get_time(self, httpclient):
        assert await httpclient.get_time()
