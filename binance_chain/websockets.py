import asyncio
import json
import logging
from random import random
from typing import Dict, Callable, Awaitable, Optional, List

import websockets as ws


class ReconnectingWebsocket:

    MAX_RECONNECTS: int = 5
    MAX_RECONNECT_SECONDS: int = 60
    MIN_RECONNECT_WAIT = 0.1
    TIMEOUT: int = 10
    PROTOCOL_VERSION: str = '1.0.0'

    def __init__(self, loop, coro, address, endpoint_url):
        self._loop = loop
        self._log = logging.getLogger(__name__)
        self._coro = coro
        self._reconnect_attempts: int = 0
        self._conn = None
        self._endpoint_url = endpoint_url
        self._address = address
        self._connect_id: int = None
        self._ping_timeout = 60
        self._socket: Optional[ws.client.WebSocketClientProtocol] = None

        self._connect()

    def _connect(self):
        self._conn = asyncio.ensure_future(self._run())

    def get_ws_endpoint_url(self):
        return f"{self._endpoint_url}ws/{self._address}"

    async def _run(self):

        keep_waiting: bool = True

        logging.info(f"connecting to {self.get_ws_endpoint_url()}")
        async with ws.connect(self.get_ws_endpoint_url(), ssl=True) as socket:
            self._socket = socket
            self._reconnect_attempts = 0

            try:
                while keep_waiting:
                    try:
                        evt = await asyncio.wait_for(self._socket.recv(), timeout=self._ping_timeout)
                    except asyncio.TimeoutError:
                        self._log.debug("no message in {} seconds".format(self._ping_timeout))
                        await self.send_keepalive()
                    except asyncio.CancelledError:
                        self._log.debug("cancelled error")
                        await self._socket.ping()
                    else:
                        try:
                            evt_obj = json.loads(evt)
                        except ValueError:
                            pass
                        else:
                            await self._coro(evt_obj)
            except ws.ConnectionClosed as e:
                self._log.debug('conn closed:{}'.format(e))
                keep_waiting = False
                await self._reconnect()
            except Exception as e:
                self._log.debug('ws exception:{}'.format(e))
                keep_waiting = False
                await self._reconnect()

    async def _reconnect(self):
        await self.cancel()
        self._reconnect_attempts += 1
        if self._reconnect_attempts < self.MAX_RECONNECTS:

            self._log.debug(f"websocket reconnecting {self.MAX_RECONNECTS - self._reconnect_attempts} attempts left")
            reconnect_wait = self._get_reconnect_wait(self._reconnect_attempts)
            self._log.debug(f' waiting {reconnect_wait}')
            await asyncio.sleep(reconnect_wait)
            self._connect()
        else:
            # maybe raise an exception
            self._log.error(f"websocket could not reconnect after {self._reconnect_attempts} attempts")
            pass

    def _get_reconnect_wait(self, attempts: int) -> int:
        expo = 2 ** attempts
        return round(random() * min(self.MAX_RECONNECT_SECONDS, expo - 1) + 1)

    async def send_keepalive(self):
        msg = {"method": "keepAlive"}
        await self._socket.send(json.dumps(msg, separators=(',', ':'), ensure_ascii=False))

    async def send_message(self, msg, retry_count=0):
        if not self._socket:
            if retry_count < 5:
                await asyncio.sleep(1)
                await self.send_message(msg, retry_count + 1)
        else:
            await self._socket.send(json.dumps(msg, separators=(',', ':'), ensure_ascii=False))

    async def cancel(self):
        try:
            self._conn.cancel()
        except asyncio.CancelledError:
            pass


class BinanceChainSocketManager:

    def __init__(self):
        """Initialise the BinanceChainSocketManager

        """
        self._callback: Callable[[int], Awaitable[str]]
        self._conn = None
        self._loop = None
        self._log = logging.getLogger(__name__)

    @classmethod
    async def create(cls, loop, callback: Callable[[int], Awaitable[str]],
                     address: str, endpoint_url: Optional[str] = None):
        self = BinanceChainSocketManager()
        self._loop = loop
        self._callback = callback
        self._endpoint_url = endpoint_url or 'wss://testnet-dex.binance.org/api/'
        self._conn = ReconnectingWebsocket(loop, self._recv, address, self._endpoint_url)
        return self

    async def _recv(self, msg: Dict):
        await self._callback(msg)

    async def subscribe(self, topic: str):
        """Subscribe to a channel

        :param topic: required
        :returns: None

        Sample ws response

        .. code-block:: python

            {
                "type":"message",
                "topic":"/market/ticker:BTC-USDT",
                "subject":"trade.ticker",
                "data":{
                    "sequence":"1545896668986",
                    "bestAsk":"0.08",
                    "size":"0.011",
                    "bestBidSize":"0.036",
                    "price":"0.08",
                    "bestAskSize":"0.18",
                    "bestBid":"0.049"
                }
            }

        Error response

        .. code-block:: python

            {
                'code': 404,
                'data': 'topic /market/ticker:BTC-USDT is not found',
                'id': '1550868034537',
                'type': 'error'
            }

        """

        req_msg = {
            'type': 'subscribe',
            'topic': topic,
            'response': True
        }

        await self._conn.send_message(req_msg)

    async def subscribe_market_depth(self, symbols: List[str]):

        req_msg = {
            "method": "subscribe",
            "topic": "marketDepth",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def subscribe_market_delta(self, symbols: List[str]):

        req_msg = {
            "method": "subscribe",
            "topic": "marketDelta",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def subscribe_trades(self, symbols: List[str]):

        req_msg = {
            "method": "subscribe",
            "topic": "trades",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def subscribe_ticker(self, symbols: List[str]):

        req_msg = {
            "method": "subscribe",
            "topic": "ticker",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def subscribe_orders(self, address: str):

        req_msg = {
            "method": "subscribe",
            "topic": "orders",
            "address": address
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe(self, topic: str):
        """Unsubscribe from a topic

        :param topic: required

        :returns: None

        Sample ws response

        .. code-block:: python

            {
                "id": "1545910840805",
                "type": "ack"
            }

        """

        req_msg = {
            'type': 'unsubscribe',
            'topic': topic,
            'response': True
        }

        await self._conn.send_message(req_msg)

    async def unsubscribe_orders(self):

        req_msg = {
            "method": "unsubscribe",
            "topic": "orders"
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_market_depth(self, symbols: List[str]):
        req_msg = {
            "method": "unsubscribe",
            "topic": "marketDepth",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_market_delta(self, symbols: List[str]):
        req_msg = {
            "method": "unsubscribe",
            "topic": "marketDelta",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_trades(self, symbols: List[str]):
        req_msg = {
            "method": "unsubscribe",
            "topic": "trades",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_ticker(self, symbols: List[str]):
        req_msg = {
            "method": "unsubscribe",
            "topic": "ticker",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)
