import asyncio
from typing import Callable, Awaitable, Optional, Dict

from binance_chain.node_rpc.http import HttpRpcClient
from binance_chain.websockets import ReconnectingWebsocket, BinanceChainSocketManagerBase
from binance_chain.environment import BinanceEnvironment
from binance_chain.constants import RpcBroadcastRequestType
from binance_chain.messages import Msg
from binance_chain.node_rpc.request import RpcRequest


class ReconnectingRpcWebsocket(ReconnectingWebsocket):

    def _get_ws_endpoint_url(self):
        return f"{self._env.wss_url}/websocket"

    async def send_keepalive(self):
        await self.send_rpc_message('keepAlive')

    async def send_rpc_message(self, method, params=None, retry_count=0):
        if not self._socket:
            if retry_count < 5:
                await asyncio.sleep(1)
                await self.send_rpc_message(method, params, retry_count + 1)
        else:
            req = RpcRequest(method, params)
            await self._socket.send(str(req))

    async def ping(self):
        await self.send_rpc_message('ping')

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
        await self._conn.send_rpc_message('subscribe', req_msg)

    async def unsubscribe(self, query):
        """Unsubscribe from events via WebSocket.

        https://binance-chain.github.io/api-reference/node-rpc.html#unsubscribe

        """
        req_msg = {
            "query": query
        }
        await self._conn.send_rpc_message('unsubscribe', req_msg)

    async def unsubscribe_all(self):
        """Unsubscribe from events via WebSocket.

        https://binance-chain.github.io/api-reference/node-rpc.html#unsubscribeall

        """
        await self._conn.send_rpc_message('unsubscribe_all')

    async def get_abci_info(self):
        await self._conn.send_rpc_message('abci_info')
    get_abci_info.__doc__ = HttpRpcClient.get_abci_info.__doc__

    async def get_consensus_state(self):
        await self._conn.send_rpc_message('consensus_state')
    get_consensus_state.__doc__ = HttpRpcClient.get_consensus_state.__doc__

    async def dump_consensus_state(self):
        await self._conn.send_rpc_message('dump_consensus_state')
    dump_consensus_state.__doc__ = HttpRpcClient.dump_consensus_state.__doc__

    async def get_genesis(self):
        await self._conn.send_rpc_message('genesis')
    dump_consensus_state.__doc__ = HttpRpcClient.dump_consensus_state.__doc__

    async def get_net_info(self):
        await self._conn.send_rpc_message('net_info')
    get_net_info.__doc__ = HttpRpcClient.get_net_info.__doc__

    async def get_num_unconfirmed_txs(self):
        await self._conn.send_rpc_message('num_unconfirmed_txs')
    get_num_unconfirmed_txs.__doc__ = HttpRpcClient.get_num_unconfirmed_txs.__doc__

    async def get_status(self):
        await self._conn.send_rpc_message('status')
    get_status.__doc__ = HttpRpcClient.get_status.__doc__

    async def get_health(self):
        await self._conn.send_rpc_message('health')
    get_health.__doc__ = HttpRpcClient.get_health.__doc__

    async def get_unconfirmed_txs(self):
        await self._conn.send_rpc_message('unconfirmed_txs')
    get_unconfirmed_txs.__doc__ = HttpRpcClient.get_unconfirmed_txs.__doc__

    async def get_validators(self):
        await self._conn.send_rpc_message('validators')
    get_validators.__doc__ = HttpRpcClient.get_validators.__doc__

    async def abci_query(self, data: str, path: Optional[str] = None,
                         prove: Optional[bool] = None, height: Optional[int] = None):
        data = {
            'data': data
        }
        if path:
            data['path'] = path
        if prove:
            data['prove'] = str(prove)
        if height:
            data['height'] = str(height)

        await self._conn.send_rpc_message('abci_query', data)
    abci_query.__doc__ = HttpRpcClient.abci_query.__doc__

    async def get_block(self, height: Optional[int] = None):
        data = {
            'height': str(height) if height else None
        }
        await self._conn.send_rpc_message('block', data)
    get_block.__doc__ = HttpRpcClient.get_block.__doc__

    async def get_block_result(self, height: int):
        data = {
            'height': str(height)
        }
        await self._conn.send_rpc_message('block_result', data)
    get_block_result.__doc__ = HttpRpcClient.get_block_result.__doc__

    async def get_block_commit(self, height: int):
        data = {
            'height': str(height)
        }
        await self._conn.send_rpc_message('commit', data)
    get_block_commit.__doc__ = HttpRpcClient.get_block_commit.__doc__

    async def get_blockchain_info(self, min_height: int, max_height: int):
        assert max_height > min_height

        data = {
            'minHeight': str(min_height),
            'maxHeight': str(max_height)
        }
        await self._conn.send_rpc_message('blockchain', data)
    get_blockchain_info.__doc__ = HttpRpcClient.get_blockchain_info.__doc__

    async def broadcast_msg(self, msg: Msg, request_type: RpcBroadcastRequestType = RpcBroadcastRequestType.SYNC):

        msg.wallet.initialise_wallet()
        data = msg.to_hex_data().decode()

        tx_data = {
            'tx': '0x' + data
        }

        if request_type == RpcBroadcastRequestType.ASYNC:
            tx_func = self._broadcast_tx_async
        elif request_type == RpcBroadcastRequestType.COMMIT:
            tx_func = self._broadcast_tx_commit
        else:
            tx_func = self._broadcast_tx_sync
        res = await tx_func(tx_data)

        msg.wallet.increment_account_sequence()
        return res
    broadcast_msg.__doc__ = HttpRpcClient.broadcast_msg.__doc__

    async def _broadcast_tx_async(self, tx_data: Dict):
        await self._conn.send_rpc_message('broadcast_tx_async', tx_data)
    _broadcast_tx_async.__doc__ = HttpRpcClient._broadcast_tx_async.__doc__

    async def _broadcast_tx_commit(self, tx_data: Dict):
        await self._conn.send_rpc_message('broadcast_tx_commit', tx_data)
    _broadcast_tx_commit.__doc__ = HttpRpcClient._broadcast_tx_commit.__doc__

    async def _broadcast_tx_sync(self, tx_data: Dict):
        await self._conn.send_rpc_message('broadcast_tx_sync', tx_data)
    _broadcast_tx_sync.__doc__ = HttpRpcClient._broadcast_tx_sync.__doc__

    async def get_consensus_params(self, height: Optional[int] = None):
        data = {
            'height': str(height) if height else None
        }
        await self._conn.send_rpc_message('consensus_params', data)
    get_consensus_params.__doc__ = HttpRpcClient.get_consensus_params.__doc__

    async def get_tx(self, tx_hash: str, prove: Optional[bool] = None):
        data = {
            'hash': tx_hash
        }
        if prove:
            data['prove'] = str(prove)

        await self._conn.send_rpc_message('tx', data)
    get_tx.__doc__ = HttpRpcClient.get_tx.__doc__

    async def tx_search(self, query: str, prove: Optional[bool] = None,
                        page: Optional[int] = None, limit: Optional[int] = None):
        data = {
            'query': query
        }
        if prove:
            data['prove'] = str(prove)
        if page:
            data['page'] = str(page)
        if limit:
            data['limit'] = str(limit)

        await self._conn.send_rpc_message('tx_search', data)
    tx_search.__doc__ = HttpRpcClient.tx_search.__doc__
