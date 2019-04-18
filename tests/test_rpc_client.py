import itertools

import pytest

from binance_chain.http import HttpApiClient
from binance_chain.node_rpc.http import HttpRpcClient, AsyncHttpRpcClient
from binance_chain.node_rpc.request import RpcRequest
from binance_chain.environment import BinanceEnvironment
from binance_chain.wallet import Wallet
from binance_chain.constants import PeerType


class TestHttpRpcClient:

    peers = None

    @pytest.fixture
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture
    def httpclient(self, env):
        return HttpApiClient(env=env)

    @pytest.fixture
    def private_key(self):
        return '3dcc267e1f7edca86e03f0963b2d0b7804552d3014caddcfc435a4d7bc240cf5'

    @pytest.fixture
    def wallet(self, env, private_key):
        return Wallet(private_key=private_key, env=env)

    @pytest.fixture
    def listen_address(self, httpclient):
        if not self.peers:
            self.peers = httpclient.get_peers(peer_type=PeerType.NODE)
        return self.peers[0]['listen_addr']

    @pytest.fixture
    def rpcclient(self, listen_address):
        return HttpRpcClient(endpoint_url=listen_address)

    def test_get_abci_info(self, rpcclient):
        assert rpcclient.get_abci_info()

    def test_get_block(self, rpcclient):
        assert rpcclient.get_block()

        assert rpcclient.get_block(10000)


class TestAsyncHttpRpcClient:

    peers = None

    @pytest.fixture
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture
    def httpclient(self, env):
        return HttpApiClient(env=env)

    @pytest.fixture
    def private_key(self):
        return '3dcc267e1f7edca86e03f0963b2d0b7804552d3014caddcfc435a4d7bc240cf5'

    @pytest.fixture
    def wallet(self, env, private_key):
        return Wallet(private_key=private_key, env=env)

    @pytest.fixture
    def listen_address(self, httpclient):
        if not self.peers:
            self.peers = httpclient.get_peers(peer_type=PeerType.NODE)
        return self.peers[0]['listen_addr']

    @pytest.mark.asyncio
    @pytest.fixture
    async def rpcclient(self, listen_address):
        return await AsyncHttpRpcClient.create(endpoint_url=listen_address)

    @pytest.mark.asyncio
    async def test_get_abci_info(self, rpcclient):
        assert await rpcclient.get_abci_info()

    @pytest.mark.asyncio
    async def test_get_block(self, rpcclient):
        assert await rpcclient.get_block()

        assert await rpcclient.get_block(10000)


class TestRpcRequest:

    def test_json_string_building(self):
        # reset id count
        RpcRequest.id_generator = itertools.count(1)
        req = RpcRequest("mymethod", {'param1': 'this', 'otherparam': 'that'})

        assert str(req) == '{"jsonrpc":"2.0","method":"mymethod","params":{"param1":"this","otherparam":"that"},"id":1}'

        req2 = RpcRequest("mymethod", {'param1': 'this', 'otherparam': 'that'})
        assert str(req2) == \
               '{"jsonrpc":"2.0","method":"mymethod","params":{"param1":"this","otherparam":"that"},"id":2}'
