import asyncio
from typing import Callable, Awaitable, Optional

from jsonrpcclient.clients.websockets_client import WebSocketsClient
from jsonrpcclient.requests import Request

from binance_chain.websockets import ReconnectingWebsocket, BinanceChainSocketManagerBase
from binance_chain.environment import BinanceEnvironment


class ReconnectingRpcWebsocket(ReconnectingWebsocket):

    def __init__(self, loop, coro, env: BinanceEnvironment):
        self._rcp_client = Optional[WebSocketsClient]

        super().__init__(loop, coro, env=env)

    def _get_ws_endpoint_url(self):
        return f"{self._env.wss_url}/websocket"

    def _on_connect(self, socket):
        super()._on_connect(socket)
        self._rcp_client = WebSocketsClient(socket)

    async def send_keepalive(self):
        await self._send_rpc_request('keepAlive')

    def _send_rpc_request(self, method, params=None):
        req = Request(method, params)
        self._rcp_client.request(str(req))

    async def send_rpc_message(self, method, params, retry_count=0):
        if not self._socket:
            if retry_count < 5:
                await asyncio.sleep(1)
                await self.send_rpc_message(method, params, retry_count + 1)
        else:
            await self._rcp_client.request(method, params)

    async def ping(self):
        await self._send_rpc_request('ping')

    async def cancel(self):
        try:
            self._conn.cancel()
        except asyncio.CancelledError:
            pass


class WebsocketRpcClient(BinanceChainSocketManagerBase):

    @classmethod
    async def create(cls, loop, callback: Callable[[int], Awaitable[str]], env: Optional[BinanceEnvironment] = None):
        """Create a BinanceChainSocketManager instance

        :param loop: asyncio loop
        :param callback: async callback function to receive messages
        :param env:
        :return:
        """
        env = env or BinanceEnvironment.get_production_env()
        self = WebsocketRpcClient(env=env)
        self._loop = loop
        self._callback = callback
        self._conn = ReconnectingRpcWebsocket(loop, self._recv, env=env)
        return self

    async def subscribe(self, query):
        """Subscribe for events via WebSocket.

        https://binance-chain.github.io/api-reference/node-rpc.html#subscribe

        To tell which events you want, you need to provide a query. query is a string, which has a form:
        "condition AND condition ..." (no OR at the moment). condition has a form: "key operation operand".
        key is a string with a restricted set of possible symbols ( \t\n\r\\()"'=>< are not allowed). operation
        can be "=", "<", "<=", ">", ">=", "CONTAINS". operand can be a string (escaped with single quotes),
        number, date or time.


        """
        req_msg = {
            "query": query
        }
        await self._conn.send_message(req_msg)
