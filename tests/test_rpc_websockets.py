import pytest
import asyncio

from binance_chain.http import HttpApiClient
from binance_chain.node_rpc.websockets import ReconnectingRpcWebsocket, WebsocketRpcClient
from binance_chain.environment import BinanceEnvironment


class TestRpcWebsockets:

    peers = None

    @pytest.fixture()
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture
    def httpclient(self, env):
        return HttpApiClient(env=env)

    @pytest.fixture
    def listen_address(self, httpclient):
        if not self.peers:
            self.peers = httpclient.get_node_peers()
        return self.peers[0]['listen_addr']

    @pytest.fixture()
    def ws_env(self, env, listen_address):
        listen_address = listen_address.replace('http://', 'ws://')
        listen_address = listen_address.replace('https://', 'wss://')
        return BinanceEnvironment(env.api_url, listen_address, env.hrp)

    @pytest.mark.asyncio
    async def test_rpc_websocket_connects(self, event_loop, ws_env, listen_address):

        async def callback():
            pass

        socket = ReconnectingRpcWebsocket(event_loop, callback, ws_env)

        await asyncio.sleep(2)

        assert socket._socket is not None

    @pytest.mark.asyncio
    async def test_rpc_websocket_create(self, event_loop, env):

        async def callback():
            pass

        wrc = await WebsocketRpcClient.create(event_loop, callback, env=env)

        assert wrc

        await wrc.tx_search("query", True, 1, 10)
        await wrc.get_blockchain_info(1, 1000)
        await wrc.abci_query("data_str", "path_str", True, 1000)
