import pytest

from binance_chain.depthcache import DepthCache, DepthCacheManager
from binance_chain.environment import BinanceEnvironment
from binance_chain.http import HttpApiClient


class TestDepthCache:

    clear_price = "0.00000000"

    def test_init_depth_cache(self):

        symbol = 'BNB_ETH'
        dc = DepthCache(symbol='BNB_ETH')

        assert dc.symbol == symbol
        assert len(dc.get_asks()) == 0
        assert len(dc.get_bids()) == 0

    def test_add_bid(self):

        dc = DepthCache('BNB_ETH')
        bid = [1.0, 2.0]

        dc.add_bid(bid)

        assert dc.get_bids() == [bid]
        assert len(dc.get_asks()) == 0

    def test_remove_bid(self):

        dc = DepthCache('BNB_ETH')
        bid = [1.0, 2.0]

        dc.add_bid(bid)

        bid = [1.0, self.clear_price]

        dc.add_bid(bid)

        assert len(dc.get_bids()) == 0
        assert len(dc.get_asks()) == 0

    def test_add_ask(self):

        dc = DepthCache('BNB_ETH')
        ask = [1.0, 2.0]

        dc.add_ask(ask)

        assert dc.get_asks() == [ask]
        assert len(dc.get_bids()) == 0

    def test_remove_ask(self):

        dc = DepthCache('BNB_ETH')
        ask = [1.0, 2.0]

        dc.add_ask(ask)

        ask = [1.0, self.clear_price]

        dc.add_ask(ask)

        assert len(dc.get_bids()) == 0
        assert len(dc.get_asks()) == 0

    def test_sorted_bids(self):

        dc = DepthCache('BNB_ETH')
        bid = [1.0, 2.0]

        dc.add_bid(bid)

        bid2 = [2.0, 3.0]

        dc.add_bid(bid2)

        assert dc.get_bids() == [bid2, bid]
        assert len(dc.get_asks()) == 0

    def test_sorted_asks(self):

        dc = DepthCache('BNB_ETH')
        ask = [1.0, 2.0]

        dc.add_ask(ask)

        ask2 = [2.0, 3.0]

        dc.add_ask(ask2)

        assert dc.get_asks() == [ask, ask2]
        assert len(dc.get_bids()) == 0


class TestDepthCacheConnection:

    @pytest.fixture()
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture
    def httpclient(self, env):
        return HttpApiClient(env=env)

    @pytest.mark.asyncio
    async def test_depthcache_create(self, event_loop, env):

        async def callback(_depth_cache):
            pass

        client = HttpApiClient(env=env)

        dcm1 = await DepthCacheManager.create(client, event_loop, "MITH-C76_BNB", callback, env=env)

        assert dcm1

        assert dcm1.get_depth_cache()

        await dcm1.close()
