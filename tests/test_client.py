import pytest

from binance_chain.http import HttpApiClient
from binance_chain.constants import PeerType
from binance_chain.environment import BinanceEnvironment


class TestClient:

    @pytest.fixture
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture
    def httpclient(self, env):
        return HttpApiClient(env=env)

    def test_get_time(self, httpclient):
        assert httpclient.get_time()

    def test_get_node_info(self, httpclient):
        assert httpclient.get_node_info()

    def test_get_validators(self, httpclient):
        assert httpclient.get_validators()

    def test_get_peers(self, httpclient):
        assert httpclient.get_peers()

    @pytest.mark.parametrize("peer_type", [
        PeerType.NODE,
        PeerType.WEBSOCKET
    ])
    def test_get_peers_capability_node(self, peer_type, httpclient):
        peers = httpclient.get_peers(peer_type=peer_type)
        for p in peers:
            assert peer_type in p['capabilities']

    def test_get_node_peers(self, httpclient):
        peers = httpclient.get_node_peers()
        for p in peers:
            assert PeerType.NODE in p['capabilities']
        assert httpclient.get_peers()

    def test_get_websocket_peers(self, httpclient):
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
