import pytest

from binance_chain.node_rpc.pooled_client import PooledRpcClient
from binance_chain.environment import BinanceEnvironment


class TestRpcPooled:

    @pytest.fixture()
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.mark.asyncio
    async def test_rpc_pooled_create(self, event_loop, env):

        prc = await PooledRpcClient.create(loop=event_loop, env=env)

        assert prc

        await prc.get_consensus_state()
        await prc.get_blockchain_info(1, 1000)
        await prc.get_abci_info()
