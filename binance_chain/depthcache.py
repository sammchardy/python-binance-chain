import time
import asyncio
from operator import itemgetter
from typing import Optional

from binance_chain.websockets import BinanceChainSocketManager
from binance_chain.http import HttpApiClient
from binance_chain.environment import BinanceEnvironment


class DepthCache(object):

    clear_price = "0.00000000"

    def __init__(self, symbol):
        """Initialise the DepthCache

        :param symbol: Symbol to create depth cache for
        :type symbol: string

        """
        self.symbol = symbol
        self._bids = {}
        self._asks = {}
        self.update_time = None

    def add_bid(self, bid):
        """Add a bid to the cache

        :param bid:
        :return:

        """
        if bid[1] == self.clear_price:
            del self._bids[bid[0]]
        else:
            self._bids[bid[0]] = bid[1]

    def add_ask(self, ask):
        """Add an ask to the cache

        :param ask:
        :return:

        """
        if ask[1] == self.clear_price:
            del self._asks[ask[0]]
        else:
            self._asks[ask[0]] = ask[1]

    def get_bids(self):
        """Get the current bids

        :return: list of bids with price and quantity as floats

        .. code-block:: python

            [
                [
                    0.0001946,  # Price
                    45.0        # Quantity
                ],
                [
                    0.00019459,
                    2384.0
                ],
                [
                    0.00019158,
                    5219.0
                ],
                [
                    0.00019157,
                    1180.0
                ],
                [
                    0.00019082,
                    287.0
                ]
            ]

        """
        return DepthCache.sort_depth(self._bids, reverse=True)

    def get_asks(self):
        """Get the current asks

        :return: list of asks with price and quantity as floats

        .. code-block:: python

            [
                [
                    0.0001955,  # Price
                    57.0'       # Quantity
                ],
                [
                    0.00019699,
                    778.0
                ],
                [
                    0.000197,
                    64.0
                ],
                [
                    0.00019709,
                    1130.0
                ],
                [
                    0.0001971,
                    385.0
                ]
            ]

        """
        return DepthCache.sort_depth(self._asks, reverse=False)

    @staticmethod
    def sort_depth(vals, reverse=False):
        """Sort bids or asks by price
        """
        lst = [[price, quantity] for price, quantity in vals.items()]
        lst = sorted(lst, key=itemgetter(0), reverse=reverse)
        return lst


class DepthCacheManager(object):

    _default_refresh = 60 * 30  # 30 minutes

    @classmethod
    async def create(cls, client: HttpApiClient, loop, symbol: str, coro=None, refresh_interval: int = _default_refresh,
                     env: Optional[BinanceEnvironment] = None):
        """Create a DepthCacheManager instance

        :param client: Binance API client
        :param loop:
        :param symbol: Symbol to create depth cache for
        :param coro: Optional coroutine to receive depth cache updates
        :type coro: async coroutine
        :param env: Optional coroutine to receive depth cache updates
        :param refresh_interval: Optional number of seconds between cache refresh, use 0 or None to disable

        """
        self = DepthCacheManager()
        self._client = client
        self._loop = loop
        self._symbol = symbol
        self._coro = coro
        self._last_update_id = None
        self._depth_message_buffer = []
        self._bm = None
        self._depth_cache = DepthCache(self._symbol)
        self._refresh_interval = refresh_interval
        self._env = env or BinanceEnvironment.get_production_env()

        await self._start_socket()
        await self._init_cache()

        return self

    async def _init_cache(self):
        """Initialise the depth cache calling REST endpoint

        :return:
        """
        self._last_update_time = None
        self._depth_message_buffer = []

        res = self._client.get_order_book(self._symbol)
        print(f"got res:{res}")

        # process bid and asks from the order book
        for bid in res['bids']:
            self._depth_cache.add_bid(bid)
        for ask in res['asks']:
            self._depth_cache.add_ask(ask)

        # set first update id
        self._last_update_time = int(time.time())

        # set a time to refresh the depth cache
        if self._refresh_interval:
            self._refresh_time = int(time.time()) + self._refresh_interval

        # Apply any updates from the websocket
        for msg in self._depth_message_buffer:
            await self._process_depth_message(msg, buffer=True)

        # clear the depth buffer
        del self._depth_message_buffer

        # call the callback with the updated depth cache
        if self._coro:
            await self._coro(self._depth_cache)

    async def _start_socket(self):
        """Start the depth cache socket

        :return:
        """
        self._bm = await BinanceChainSocketManager.create(self._loop, self._depth_event, self._env)
        await self._bm.subscribe_market_diff(symbols=[self._symbol])

        # wait for some socket responses
        while not len(self._depth_message_buffer):
            await asyncio.sleep(1)

    async def _depth_event(self, msg):
        """Handle a depth event

        :param msg:
        :return:

        """

        # TODO: handle errors in message

        if self._last_update_time is None:
            # Initial depth snapshot fetch not yet performed, buffer messages
            self._depth_message_buffer.append(msg)
        else:
            await self._process_depth_message(msg)

    async def _process_depth_message(self, msg, buffer=False):
        """Process a depth event message.

        :param msg: Depth event message.
        :return:

        """

        if buffer and msg['data']['E'] < self._last_update_time:
            # ignore any updates before the initial update id
            return

        # add any bid or ask values
        for bid in msg['data']['b']:
            self._depth_cache.add_bid(bid)
        for ask in msg['data']['a']:
            self._depth_cache.add_ask(ask)

        # keeping update time
        self._depth_cache.update_time = msg['data']['E']

        # call the callback with the updated depth cache
        if self._coro:
            await self._coro(self._depth_cache)

        self._last_update_time = msg['data']['E']

        # after processing event see if we need to refresh the depth cache
        if self._refresh_interval and int(time.time()) > self._refresh_time:
            await self._init_cache()

    def get_depth_cache(self):
        """Get the current depth cache

        :return: DepthCache object

        """
        return self._depth_cache

    async def close(self):
        """Close the open socket for this manager

        :return:
        """
        await self._bm.close()
        self._depth_cache = None
