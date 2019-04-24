import asyncio
import json
import logging
from random import random
from typing import Dict, Callable, Awaitable, Optional, List

import websockets as ws
from binance_chain.environment import BinanceEnvironment
from binance_chain.constants import KlineInterval


class ReconnectingWebsocket:

    MAX_RECONNECTS: int = 5
    MAX_RECONNECT_SECONDS: int = 60
    MIN_RECONNECT_WAIT = 0.1
    TIMEOUT: int = 10
    PROTOCOL_VERSION: str = '1.0.0'

    def __init__(self, loop, coro, env: BinanceEnvironment):
        self._loop = loop
        self._log = logging.getLogger(__name__)
        self._coro = coro
        self._reconnect_attempts: int = 0
        self._conn = None
        self._env = env
        self._connect_id: int = None
        self._ping_timeout = 60
        self._socket: Optional[ws.client.WebSocketClientProtocol] = None

        self._connect()

    def _connect(self):
        self._conn = asyncio.ensure_future(self._run())

    def _get_ws_endpoint_url(self):
        return f"{self._env.wss_url}ws"

    async def _run(self):

        keep_waiting: bool = True

        logging.info(f"connecting to {self._get_ws_endpoint_url()}")
        try:
            async with ws.connect(self._get_ws_endpoint_url(), loop=self._loop) as socket:
                self._on_connect(socket)

                try:
                    while keep_waiting:
                        try:
                            evt = await asyncio.wait_for(self._socket.recv(), timeout=self._ping_timeout)
                        except asyncio.TimeoutError:
                            self._log.debug("no message in {} seconds".format(self._ping_timeout))
                            await self.send_keepalive()
                        except asyncio.CancelledError:
                            self._log.debug("cancelled error")
                            await self.ping()
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
        except Exception as e:
            logging.info(f"websocket error: {e}")

    def _on_connect(self, socket):
        self._socket = socket
        self._reconnect_attempts = 0

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
                logging.info("Unable to send, not connected")
        else:
            await self._socket.send(json.dumps(msg, separators=(',', ':'), ensure_ascii=False))

    async def ping(self):
        await self._socket.ping()

    async def cancel(self):
        try:
            self._conn.cancel()
        except asyncio.CancelledError:
            pass


class BinanceChainSocketManagerBase:

    def __init__(self, env: BinanceEnvironment):
        """Initialise the BinanceChainSocketManager

        """
        self._env = env
        self._callback: Callable[[int], Awaitable[str]]
        self._conn = None
        self._loop = None
        self._log = logging.getLogger(__name__)

    @classmethod
    async def create(cls, loop, callback: Callable[[int], Awaitable[str]], env: Optional[BinanceEnvironment] = None):
        """Create a BinanceChainSocketManager instance

        :param loop: asyncio loop
        :param callback: async callback function to receive messages
        :param env:
        :return:
        """
        env = env or BinanceEnvironment.get_production_env()
        self = BinanceChainSocketManager(env=env)
        self._loop = loop
        self._callback = callback
        self._conn = ReconnectingWebsocket(loop, self._recv, env=env)
        return self

    async def _recv(self, msg: Dict):
        await self._callback(msg)


class BinanceChainSocketManager(BinanceChainSocketManagerBase):

    async def subscribe_market_depth(self, symbols: List[str]):
        """Top 20 levels of bids and asks.

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#6-book-depth-streams

        :param symbols:
        :return:

        Sample ws response

        .. code-block:: python

            {
                "stream": "marketDepth",
                "data": {
                    "lastUpdateId": 160,    // Last update ID
                    "symbol": "BNB_BTC",    // symbol
                    "bids": [               // Bids to be updated
                        [
                        "0.0024",           // Price level to be updated
                        "10"                // Quantity
                        ]
                    ],
                    "asks": [               // Asks to be updated
                        [
                        "0.0026",           // Price level to be updated
                        "100"               // Quantity
                        ]
                    ]
                }
            }

        """

        req_msg = {
            "method": "subscribe",
            "topic": "marketDepth",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def subscribe_market_diff(self, symbols: List[str]):
        """Returns individual trade updates.

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#5-diff-depth-stream

        :param symbols:
        :return:

        Sample ws response

        .. code-block:: python

            {
                "stream": "marketDiff",
                "data": {
                    "e": "depthUpdate",   // Event type
                    "E": 123456789,       // Event time
                    "s": "BNB_BTC",       // Symbol
                    "b": [                // Bids to be updated
                        [
                        "0.0024",         // Price level to be updated
                        "10"              // Quantity
                        ]
                    ],
                    "a": [                // Asks to be updated
                        [
                        "0.0026",         // Price level to be updated
                        "100"             // Quantity
                        ]
                    ]
                }
            }

        """

        req_msg = {
            "method": "subscribe",
            "topic": "marketDiff",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def subscribe_trades(self, symbols: List[str]):
        """Returns individual trade updates.

        :param symbols:
        :return:

        Sample ws response

        .. code-block:: python

            {
                "stream": "trades",
                "data": [{
                    "e": "trade",       // Event type
                    "E": 123456789,     // Event height
                    "s": "BNB_BTC",     // Symbol
                    "t": "12345",       // Trade ID
                    "p": "0.001",       // Price
                    "q": "100",         // Quantity
                    "b": "88",          // Buyer order ID
                    "a": "50",          // Seller order ID
                    "T": 123456785,     // Trade time
                    "sa": "bnb1me5u083m2spzt8pw8vunprnctc8syy64hegrcp", // SellerAddress
                    "ba": "bnb1kdr00ydr8xj3ydcd3a8ej2xxn8lkuja7mdunr5" // BuyerAddress
                },
                {
                    "e": "trade",       // Event type
                    "E": 123456795,     // Event time
                    "s": "BNB_BTC",     // Symbol
                    "t": "12348",       // Trade ID
                    "p": "0.001",       // Price
                    "q": "100",         // Quantity
                    "b": "88",          // Buyer order ID
                    "a": "52",          // Seller order ID
                    "T": 123456795,     // Trade time
                    "sa": "bnb1me5u083m2spzt8pw8vunprnctc8syy64hegrcp", // SellerAddress
                    "ba": "bnb1kdr00ydr8xj3ydcd3a8ej2xxn8lkuja7mdunr5" // BuyerAddress
                }]
            }

        """

        req_msg = {
            "method": "subscribe",
            "topic": "trades",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def subscribe_ticker(self, symbols: Optional[List[str]]):
        """24hr Ticker statistics for a symbols are pushed every second.

        Default is all symbols, otherwise specify a list of symbols to watch

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#8-individual-symbol-ticker-streams
        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#9-all-symbols-ticker-streams

        :param symbols: optional
        :return:

        Sample ws response

        .. code-block:: python

            {
              "stream": "ticker",
              "data": {
                "e": "24hrTicker",  // Event type
                "E": 123456789,     // Event time
                "s": "BNBBTC",      // Symbol
                "p": "0.0015",      // Price change
                "P": "250.00",      // Price change percent
                "w": "0.0018",      // Weighted average price
                "x": "0.0009",      // Previous day's close price
                "c": "0.0025",      // Current day's close price
                "Q": "10",          // Close trade's quantity
                "b": "0.0024",      // Best bid price
                "B": "10",          // Best bid quantity
                "a": "0.0026",      // Best ask price
                "A": "100",         // Best ask quantity
                "o": "0.0010",      // Open price
                "h": "0.0025",      // High price
                "l": "0.0010",      // Low price
                "v": "10000",       // Total traded base asset volume
                "q": "18",          // Total traded quote asset volume
                "O": 0,             // Statistics open time
                "C": 86400000,      // Statistics close time
                "F": "0",           // First trade ID
                "L": "18150",       // Last trade Id
                "n": 18151          // Total number of trades
              }
            }

        """

        topic = 'ticker'
        if not symbols:
            topic = 'allTickers'
            symbols = ['$all']

        req_msg = {
            "method": "subscribe",
            "topic": topic,
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def subscribe_mini_ticker(self, symbol: Optional[str]):
        """Compact ticker for all or a single symbol

        Default is all symbols, otherwise specify a symbol to watch

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#10-individual-symbol-mini-ticker-streams
        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#11-all-symbols-mini-ticker-streams

        :param symbol: optional
        :return:

        Sample ws response

        .. code-block:: python

            {
              "stream": "allMiniTickers",
              "data": [
                {
                  "e": "24hrMiniTicker",      // Event type
                  "E": 123456789,             // Event time
                  "s": "BNBBTC",              // Symbol
                  "c": "0.0025",              // Current day's close price
                  "o": "0.0010",              // Open price
                  "h": "0.0025",              // High price
                  "l": "0.0010",              // Low price
                  "v": "10000",               // Total traded base asset volume
                  "q": "18",                  // Total traded quote asset volume
                },
                {
                  ...
                }]
            }

        """

        if not symbol:
            topic = 'allMiniTickers'
            symbol_list = ['$all']
        else:
            topic = 'miniTicker'
            symbol_list = [symbol]

        req_msg = {
            "method": "subscribe",
            "topic": topic,
            "symbols": symbol_list
        }
        await self._conn.send_message(req_msg)

    async def subscribe_blockheight(self):
        """Streams the latest block height.

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#12-blockheight

        :return:

        Sample ws response

        .. code-block:: python

            {
              "stream": "blockheight",
              "data": {
                "h": 123456789,     // Block height
              }
            }

        """

        req_msg = {
            "method": "subscribe",
            "topic": 'blockheight',
            "symbols": ["$all"]
        }
        await self._conn.send_message(req_msg)

    async def subscribe_orders(self, address: str):
        """Returns individual order updates.

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#1-orders

        :param address: address to watch
        :return:

        Sample ws response

        .. code-block:: python

            {
                "stream": "orders",
                "data": [{
                    "e": "executionReport",        // Event type
                    "E": 1499405658658,            // Event height
                    "s": "ETH_BTC",                // Symbol
                    "S": 1,                        // Side, 1 for Buy; 2 for Sell
                    "o": 2,                        // Order type, 2 for LIMIT (only)
                    "f": 1,                        // Time in force,  1 for Good Till Expire (GTE); 3 for Immediate Or Cancel (IOC)
                    "q": "1.00000000",             // Order quantity
                    "p": "0.10264410",             // Order price
                    "x": "NEW",                    // Current execution type
                    "X": "Ack",                    // Current order status, possible values Ack, Canceled, Expired, IocNoFill, PartialFill, FullyFill, FailedBlocking, FailedMatching, Unknown
                    "i": "91D9...7E18-2317",       // Order ID
                    "l": "0.00000000",             // Last executed quantity
                    "z": "0.00000000",             // Cumulative filled quantity
                    "L": "0.00000000",             // Last executed price
                    "n": "10000BNB",               // Commission amount for all user trades within a given block. Fees will be displayed with each order but will be charged once.
                                                   // Fee can be composed of a single symbol, ex: "10000BNB"
                                                   // or multiple symbols if the available "BNB" balance is not enough to cover the whole fees, ex: "1.00000000BNB;0.00001000BTC;0.00050000ETH"
                    "T": 1499405658657,            // Transaction time
                    "t": "TRD1",                   // Trade ID
                    "O": 1499405658657,            // Order creation time
                },
                {
                    "e": "executionReport",        // Event type
                    "E": 1499405658658,            // Event height
                    "s": "ETH_BNB",                // Symbol
                    "S": "BUY",                    // Side
                    "o": "LIMIT",                  // Order type
                    "f": "GTE",                    // Time in force
                    "q": "1.00000000",             // Order quantity
                    "p": "0.10264410",             // Order price
                    "x": "NEW",                    // Current execution type
                    "X": "Ack",                    // Current order status
                    "i": 4293154,                  // Order ID
                    "l": "0.00000000",             // Last executed quantity
                    "z": "0.00000000",             // Cumulative filled quantity
                    "L": "0.00000000",             // Last executed price
                    "n": "10000BNB",               // Commission amount for all user trades within a given block. Fees will be displayed with each order but will be charged once.
                                                    // Fee can be composed of a single symbol, ex: "10000BNB"
                                                    // or multiple symbols if the available "BNB" balance is not enough to cover the whole fees, ex: "1.00000000BNB;0.00001000BTC;0.00050000ETH"
                    "T": 1499405658657,            // Transaction time
                    "t": "TRD2",                   // Trade ID
                    "O": 1499405658657,            // Order creation time
                }]
            }

        """

        req_msg = {
            "method": "subscribe",
            "topic": "orders",
            "userAddress": address
        }
        await self._conn.send_message(req_msg)

    async def subscribe_account(self, address: str):
        """Return account updates.

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#2-account

        :param address: address to watch
        :return:

        Sample ws response

        .. code-block:: python

            {
                "stream": "accounts",
                "data": [{
                  "e": "outboundAccountInfo",   // Event type
                  "E": 1499405658849,           // Event height
                  "B": [                        // Balances array
                    {
                      "a": "LTC",               // Asset
                      "f": "17366.18538083",    // Free amount
                      "l": "0.00000000",        // Locked amount
                      "r": "0.00000000"         // Frozen amount
                    },
                    {
                      "a": "BTC",
                      "f": "10537.85314051",
                      "l": "2.19464093",
                      "r": "0.00000000"
                    },
                    {
                      "a": "ETH",
                      "f": "17902.35190619",
                      "l": "0.00000000",
                      "r": "0.00000000"
                    }
                  ]
                }]
            }

        """

        req_msg = {
            "method": "subscribe",
            "topic": "accounts",
            "userAddress": address
        }
        await self._conn.send_message(req_msg)

    async def subscribe_transfers(self, address: str):
        """Return transfer updates if userAddress is involved (as sender or receiver) in a transfer.
        Multisend is also covered

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#3-transfer

        :param address: address to watch
        :return:

        Sample ws response

        .. code-block:: python

            {
              "stream": "transfers",
              "data": {
                "e":"outboundTransferInfo",                                                // Event type
                "E":12893,                                                                 // Event height
                "H":"0434786487A1F4AE35D49FAE3C6F012A2AAF8DD59EC860DC7E77123B761DD91B",    // Transaction hash
                "f":"bnb1z220ps26qlwfgz5dew9hdxe8m5malre3qy6zr9",                          // From addr
                "t":
                  [{
                    "o":"bnb1xngdalruw8g23eqvpx9klmtttwvnlk2x4lfccu",                      // To addr
                    "c":[{                                                                 // Coins
                      "a":"BNB",                                                           // Asset
                      "A":"100.00000000"                                                   // Amount
                      }]
                  }]
              }
            }

        """

        req_msg = {
            "method": "subscribe",
            "topic": "transfers",
            "userAddress": address
        }
        await self._conn.send_message(req_msg)

    async def subscribe_klines(self, symbols: List[str], interval: KlineInterval = KlineInterval.FIVE_MINUTES):
        """The kline/candlestick stream pushes updates to the current klines/candlestick every second.

        https://binance-chain.github.io/api-reference/dex-api/ws-streams.html#7-klinecandlestick-streams

        :param symbols:
        :param interval:
        :return:

        Sample ws response

        .. code-block:: python

            {
              "stream": "kline_1m",
              "data": {
                "e": "kline",         // Event type
                "E": 123456789,       // Event time
                "s": "BNBBTC",        // Symbol
                "k": {
                  "t": 123400000,     // Kline start time
                  "T": 123460000,     // Kline close time
                  "s": "BNBBTC",      // Symbol
                  "i": "1m",          // Interval
                  "f": "100",         // First trade ID
                  "L": "200",         // Last trade ID
                  "o": "0.0010",      // Open price
                  "c": "0.0020",      // Close price
                  "h": "0.0025",      // High price
                  "l": "0.0015",      // Low price
                  "v": "1000",        // Base asset volume
                  "n": 100,           // Number of trades
                  "x": false,         // Is this kline closed?
                  "q": "1.0000",      // Quote asset volume
                }
              }
            }

        """

        req_msg = {
            "method": "subscribe",
            "topic": f"kline_{interval.value}",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_orders(self):

        req_msg = {
            "method": "unsubscribe",
            "topic": "orders"
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_account(self):

        req_msg = {
            "method": "unsubscribe",
            "topic": "accounts"
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_transfers(self):
        req_msg = {
            "method": "unsubscribe",
            "topic": "transfers"
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_market_depth(self, symbols: List[str]):
        """

        :param symbols: List of symbols to unsubscribe from
        :return:
        """
        req_msg = {
            "method": "unsubscribe",
            "topic": "marketDepth",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_market_diff(self, symbols: List[str]):
        """

        :param symbols: List of symbols to unsubscribe from
        :return:
        """
        req_msg = {
            "method": "unsubscribe",
            "topic": "marketDiff",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_trades(self, symbols: List[str]):
        """

        :param symbols: List of symbols to unsubscribe from
        :return:
        """
        req_msg = {
            "method": "unsubscribe",
            "topic": "trades",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_klines(self, symbols: List[str], interval: KlineInterval):
        """

        :param symbols: List of symbols to unsubscribe from
        :param interval:
        :return:
        """
        req_msg = {
            "method": "unsubscribe",
            "topic": f"kline_{interval.value}",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_ticker(self, symbols: Optional[List[str]]):
        if not symbols:
            req_msg = {
                "method": "unsubscribe",
                "topic": "allTickers"
            }
            await self._conn.send_message(req_msg)

        req_msg = {
            "method": "unsubscribe",
            "topic": "ticker",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_mini_ticker(self, symbols: Optional[List[str]]):
        if not symbols:
            req_msg = {
                "method": "unsubscribe",
                "topic": "allMiniTickers"
            }
            await self._conn.send_message(req_msg)

        req_msg = {
            "method": "unsubscribe",
            "topic": "miniTicker",
            "symbols": symbols
        }
        await self._conn.send_message(req_msg)

    async def unsubscribe_blockheight(self):
        req_msg = {
            "method": "unsubscribe",
            "topic": "blockheight",
            "symbols": ["$all"]
        }
        await self._conn.send_message(req_msg)

    async def close_connection(self):
        req_msg = {
            "method": "close"
        }

        await self._conn.send_message(req_msg)
