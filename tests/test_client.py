import pytest

from binance_chain.client import Client, PeerType


class TestClient:

    def setup(self):
        self.client = Client()

    def test_get_time(self):
        assert self.client.get_time()

    def test_get_node_info(self):
        assert self.client.get_node_info()

    def test_get_validators(self):
        assert self.client.get_validators()

    def test_get_peers(self):
        assert self.client.get_peers()

    @pytest.mark.parametrize("peer_type", [
        PeerType.NODE,
        PeerType.WEBSOCKET
    ])
    def test_get_peers_capability_node(self, peer_type):
        peers = self.client.get_peers(peer_type=peer_type)
        print(peers)
        for p in peers:
            assert peer_type in p['capabilities']

    def test_get_tokens(self):
        assert self.client.get_tokens()

    def test_get_markets(self):
        assert self.client.get_markets()

    def test_get_fees(self):
        assert self.client.get_fees()
