import pytest
from binance_chain.http import HttpApiClient
from binance_chain.node_rpc.http import HttpRpcClient
from binance_chain.environment import BinanceEnvironment
from binance_chain.wallet import Wallet
from binance_chain.constants import PeerType


class TestHttpRpcClient:

    @pytest.fixture()
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture()
    def httpclient(self, env):
        return HttpApiClient(env=env)

    @pytest.fixture()
    def private_key(self):
        return '3dcc267e1f7edca86e03f0963b2d0b7804552d3014caddcfc435a4d7bc240cf5'

    @pytest.fixture()
    def wallet(self, env, private_key):
        return Wallet(private_key=private_key, env=env)

    @pytest.fixture()
    def listen_address(self, httpclient):
        peers = httpclient.get_peers(peer_type=PeerType.NODE)
        return peers[0]['listen_addr']

    @pytest.fixture()
    def rpcclient(self, listen_address):
        return HttpRpcClient(endpoint_url=listen_address)

    def test_get_abci_info(self, rpcclient):
        assert rpcclient.get_abci_info()
