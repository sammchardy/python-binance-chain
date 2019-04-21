import json
import os

import pytest
import requests_mock

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

    def load_fixture(self, file_name):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        with open(f'{this_dir}/fixtures/{file_name}', 'r') as f:
            return json.load(f)

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
