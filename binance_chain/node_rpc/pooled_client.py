import asyncio
from typing import Optional


from binance_chain.http import AsyncHttpApiClient
from binance_chain.environment import BinanceEnvironment
from binance_chain.node_rpc.http import AsyncHttpRpcClient
from binance_chain.constants import RpcBroadcastRequestType
from binance_chain.messages import Msg


class PooledRpcClient:
    """RPC Node client pooling connections across available peer nodes.

    Each request uses a new node to increase API request limits

    """

    def __init__(self, env: Optional[BinanceEnvironment] = None):

        self._env = env
        self._clients = [AsyncHttpRpcClient]
        self._loop = None
        self._client_idx = 0

    @classmethod
    async def create(cls, loop=None, env: Optional[BinanceEnvironment] = None) -> 'PooledRpcClient':

        self = PooledRpcClient(env=env)
        self._loop = loop or asyncio.get_event_loop()

        await self.initialise_clients()

        return self

    async def initialise_clients(self) -> None:
        """Initialise the client connections used

        :return:
        """
        client = await AsyncHttpApiClient.create(loop=self._loop, env=self._env)
        peers = await client.get_node_peers()

        self._clients = []
        for peer in peers:
            print(f"creating client {peer['listen_addr']}")
            self._clients.append(await AsyncHttpRpcClient.create(endpoint_url=peer['listen_addr']))

    @property
    def num_peers(self):
        return len(self._clients)

    async def _request(self, func_name, params=None):
        params = params or {}
        if params.get('self'):
            del params['self']
        print(params)
        client = self._get_client()
        return await getattr(client, func_name)(**params)

    def _get_client(self):
        print(f"using client {self._client_idx}")
        client = self._clients[self._client_idx]
        self._client_idx = (self._client_idx + 1) % len(self._clients)
        return client

    async def get_path_list(self):
        return await self._request('get_path_list')
    get_path_list.__doc__ = AsyncHttpRpcClient.get_path_list.__doc__

    async def get_abci_info(self):
        return await self._request('get_abci_info')
    get_abci_info.__doc__ = AsyncHttpRpcClient.get_abci_info.__doc__

    async def get_consensus_state(self):
        return await self._request('get_consensus_state')
    get_consensus_state.__doc__ = AsyncHttpRpcClient.get_consensus_state.__doc__

    async def dump_consensus_state(self):
        return await self._request('dump_consensus_state')
    dump_consensus_state.__doc__ = AsyncHttpRpcClient.dump_consensus_state.__doc__

    async def get_genesis(self):
        return await self._request('get_genesis')
    get_genesis.__doc__ = AsyncHttpRpcClient.get_genesis.__doc__

    async def get_net_info(self):
        return await self._request('get_net_info')
    get_net_info.__doc__ = AsyncHttpRpcClient.get_net_info.__doc__

    async def get_num_unconfirmed_txs(self):
        return await self._request('get_num_unconfirmed_txs')
    get_num_unconfirmed_txs.__doc__ = AsyncHttpRpcClient.get_num_unconfirmed_txs.__doc__

    async def get_status(self):
        return await self._request('get_status')
    get_status.__doc__ = AsyncHttpRpcClient.get_status.__doc__

    async def get_health(self):
        return await self._request('get_health')
    get_health.__doc__ = AsyncHttpRpcClient.get_health.__doc__

    async def get_unconfirmed_txs(self):
        return await self._request('get_unconfirmed_txs')
    get_unconfirmed_txs.__doc__ = AsyncHttpRpcClient.get_unconfirmed_txs.__doc__

    async def get_validators(self):
        return await self._request('get_validators')
    get_validators.__doc__ = AsyncHttpRpcClient.get_validators.__doc__

    async def abci_query(self, data: str, path: Optional[str] = None,
                         prove: Optional[bool] = None, height: Optional[int] = None):
        return await self._request('abci_query', locals())
    abci_query.__doc__ = AsyncHttpRpcClient.abci_query.__doc__

    async def get_block(self, height: Optional[int] = None):
        return await self._request('get_block', locals())
    get_block.__doc__ = AsyncHttpRpcClient.get_block.__doc__

    async def get_block_result(self, height: int):
        return await self._request('get_block_result', locals())
    get_block_result.__doc__ = AsyncHttpRpcClient.get_block_result.__doc__

    async def get_block_commit(self, height: int):
        return await self._request('get_block_commit', locals())
    get_block_commit.__doc__ = AsyncHttpRpcClient.get_block_commit.__doc__

    async def get_blockchain_info(self, min_height: int, max_height: int):
        return await self._request('get_blockchain_info', locals())
    get_blockchain_info.__doc__ = AsyncHttpRpcClient.get_blockchain_info.__doc__

    async def broadcast_msg(self, msg: Msg, request_type: RpcBroadcastRequestType = RpcBroadcastRequestType.SYNC):
        return await self._request('broadcast_msg', locals())
    broadcast_msg.__doc__ = AsyncHttpRpcClient.broadcast_msg.__doc__

    async def get_consensus_params(self, height: Optional[int] = None):
        return await self._request('get_consensus_params', locals())
    get_consensus_params.__doc__ = AsyncHttpRpcClient.get_consensus_params.__doc__

    async def get_tx(self, tx_hash: str, prove: Optional[bool] = None):
        return await self._request('get_tx', locals())
    get_tx.__doc__ = AsyncHttpRpcClient.get_tx.__doc__

    async def tx_search(self, query: str, prove: Optional[bool] = None,
                        page: Optional[int] = None, limit: Optional[int] = None):
        return await self._request('tx_search', locals())
    tx_search.__doc__ = AsyncHttpRpcClient.tx_search.__doc__
