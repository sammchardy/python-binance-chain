import pytest
import asyncio

from binance_chain.websockets import BinanceChainSocketManager, ReconnectingWebsocket
from binance_chain.environment import BinanceEnvironment


class TestWebsockets:

    @pytest.fixture()
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.mark.asyncio
    async def test_websocket_connects(self, event_loop, env):

        async def callback():
            pass

        socket = ReconnectingWebsocket(event_loop, callback, env)

        await asyncio.sleep(2)

        assert socket._socket is not None

    @pytest.mark.asyncio
    async def test_websocket_create(self, event_loop, env):

        async def callback():
            pass

        bcsm = await BinanceChainSocketManager.create(event_loop, callback, env=env)

        assert bcsm

        await bcsm.close_connection()

