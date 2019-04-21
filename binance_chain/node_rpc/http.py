import asyncio
import itertools
from typing import Optional, Dict

import requests
import aiohttp

from binance_chain.exceptions import BinanceChainRPCException, BinanceChainRequestException
from binance_chain.constants import RpcBroadcastRequestType
from binance_chain.messages import Msg
from binance_chain.node_rpc.request import RpcRequest


class BaseHttpRpcClient:

    id_generator = itertools.count(1)

    def __init__(self, endpoint_url, requests_params: Optional[Dict] = None):
        self._endpoint_url = endpoint_url
        self._requests_params = requests_params

        self.session = self._init_session()

    def _init_session(self):

        session = requests.session()
        session.headers.update(self._get_headers())
        return session

    def _get_rpc_request(self, path, **kwargs) -> str:

        rpc_request = RpcRequest(path, kwargs.get('data', None))

        return str(rpc_request)

    def _get_headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'python-binance-chain',
        }

    def request_kwargs(self, method, **kwargs):

        # set default requests timeout
        kwargs['timeout'] = 10

        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)

        kwargs['data'] = kwargs.get('data', {})
        kwargs['headers'] = kwargs.get('headers', {})

        if kwargs['data'] and method == 'get':
            kwargs['params'] = kwargs['data']
            del(kwargs['data'])

        if method == 'post':
            kwargs['headers']['content-type'] = 'text/plain'

        return kwargs


class HttpRpcClient(BaseHttpRpcClient):

    def _request(self, path, **kwargs):

        rpc_request = self._get_rpc_request(path, **kwargs)

        response = self.session.post(self._endpoint_url, data=rpc_request.encode(), headers=self._get_headers())

        return self._handle_response(response)

    def _request_session(self, path, params=None):

        kwargs = {
            'params': params,
            'headers': self._get_headers()
        }

        response = self.session.get(f"{self._endpoint_url}/{path}", **kwargs)

        return self._handle_session_response(response)

    @staticmethod
    def _handle_response(response):
        """Internal helper for handling API responses from the server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """

        try:
            res = response.json()

            if 'error' in res and res['error']:
                raise BinanceChainRPCException(response)

            # by default return full response
            # if it's a normal response we have a data attribute, return that
            if 'result' in res:
                res = res['result']
            return res
        except ValueError:
            raise BinanceChainRequestException('Invalid Response: %s' % response.text)

    @staticmethod
    def _handle_session_response(response):
        """Internal helper for handling API responses from the server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """

        if not str(response.status_code).startswith('2'):
            raise BinanceChainRPCException(response)
        try:
            res = response.json()

            if 'code' in res and res['code'] != "200000":
                raise BinanceChainRPCException(response)

            if 'success' in res and not res['success']:
                raise BinanceChainRPCException(response)

            # by default return full response
            # if it's a normal response we have a data attribute, return that
            if 'result' in res:
                res = res['result']
            return res
        except ValueError:
            raise BinanceChainRequestException('Invalid Response: %s' % response.text)

    def get_path_list(self):
        """Return HTML formatted list of available endpoints

        https://binance-chain.github.io/api-reference/node-rpc.html#get-the-list

        """
        res = self._request(self._endpoint_url, method="get")
        return res.content

    def get_abci_info(self):
        """Get some info about the application.

        https://binance-chain.github.io/api-reference/node-rpc.html#abciinfo

        """
        return self._request('abci_info')

    def get_consensus_state(self):
        """ConsensusState returns a concise summary of the consensus state. UNSTABLE

        https://binance-chain.github.io/api-reference/node-rpc.html#consensusstate

        """
        return self._request('consensus_state')

    def dump_consensus_state(self):
        """DumpConsensusState dumps consensus state. UNSTABLE

        https://binance-chain.github.io/api-reference/node-rpc.html#dumpconsensusstate

        """
        return self._request('dump_consensus_state')

    def get_genesis(self):
        """Get genesis file.

        https://binance-chain.github.io/api-reference/node-rpc.html#genesis

        """
        return self._request('genesis')

    def get_net_info(self):
        """Get network info.

        https://binance-chain.github.io/api-reference/node-rpc.html#netinfo

        """
        return self._request('net_info')

    def get_num_unconfirmed_txs(self):
        """Get number of unconfirmed transactions.

        https://binance-chain.github.io/api-reference/node-rpc.html#numunconfirmedtxs

        """
        return self._request('num_unconfirmed_txs')

    def get_status(self):
        """Get Tendermint status including node info, pubkey, latest block hash, app hash, block height and time.

        https://binance-chain.github.io/api-reference/node-rpc.html#status

        """
        return self._request('status')

    def get_health(self):
        """Get node health. Returns empty result (200 OK) on success, no response - in case of an error.

        https://binance-chain.github.io/api-reference/node-rpc.html#health

        """
        return self._request('health')

    def get_unconfirmed_txs(self):
        """Get unconfirmed transactions (maximum ?limit entries) including their number.

        https://binance-chain.github.io/api-reference/node-rpc.html#unconfirmedtxs

        """
        return self._request('unconfirmed_txs')

    def get_validators(self):
        """Get the validator set at the given block height. If no height is provided, it will fetch the
        current validator set.

        https://binance-chain.github.io/api-reference/node-rpc.html#validators

        """
        return self._request('validators')

    def abci_query(self, data: str, path: Optional[str] = None,
                   prove: Optional[bool] = None, height: Optional[int] = None):
        """Query the application for some information.

        https://binance-chain.github.io/api-reference/node-rpc.html#abciquery

        path	string	Path to the data ("/a/b/c")
        data	[]byte	Data
        height	int64	Height (0 means latest)
        prove	bool	Includes proof if true

        """

        data = {
            'data': data
        }
        if path:
            data['path'] = path
        if prove:
            data['prove'] = str(prove)
        if height:
            data['height'] = str(height)

        return self._request('abci_query', data=data)

    def get_block(self, height: Optional[int] = None):
        """Get block at a given height. If no height is provided, it will fetch the latest block.

        https://binance-chain.github.io/api-reference/node-rpc.html#block

        height	int64

        """

        data = {
            'height': str(height) if height else None
        }

        return self._request('block', data=data)

    def get_block_result(self, height: int):
        """BlockResults gets ABCIResults at a given height. If no height is provided, it will fetch results for the
        latest block.

        https://binance-chain.github.io/api-reference/node-rpc.html#blockresults

        height	int64

        """

        data = {
            'height': str(height)
        }

        return self._request('block_result', data=data)

    def get_block_commit(self, height: int):
        """Get block commit at a given height. If no height is provided, it will fetch the commit for the latest block.

        https://binance-chain.github.io/api-reference/node-rpc.html#commit

        height	int64	0

        """

        data = {
            'height': str(height)
        }

        return self._request('commit', data=data)

    def get_blockchain_info(self, min_height: int, max_height: int):
        """Get block headers for minHeight <= height <= maxHeight. Block headers are returned in descending order
        (highest first). Returns at most 20 items.

        https://binance-chain.github.io/api-reference/node-rpc.html#blockchaininfo

        min_height	int64	0
        max_height	int64	0

        """

        assert max_height > min_height

        data = {
            'minHeight': str(min_height),
            'maxHeight': str(max_height)
        }

        return self._request('blockchain', data=data)

    def broadcast_msg(self, msg: Msg, request_type: RpcBroadcastRequestType = RpcBroadcastRequestType.SYNC):
        """Wrapper function fro broadcasting transactions

        https://binance-chain.github.io/api-reference/node-rpc.html#broadcasttxasync

        RpcBroadcastRequestType
            SYNC - Returns with the response from CheckTx.
            ASYNC - Returns right away, with no response
            COMMIT - only returns error if mempool.CheckTx() errs or if we timeout waiting for tx to commit.

        :param msg: message object to send
        :param request_type: type of request to make
        :return:
        """

        msg.wallet.initialise_wallet()
        data = msg.to_hex_data().decode()

        tx_data = {
            'tx': '0x' + data
        }

        if request_type == RpcBroadcastRequestType.ASYNC:
            res = self._broadcast_tx_async(tx_data)
        elif request_type == RpcBroadcastRequestType.COMMIT:
            res = self._broadcast_tx_commit(tx_data)
        else:
            res = self._broadcast_tx_sync(tx_data)

        msg.wallet.increment_account_sequence()
        return res

    def _broadcast_tx_async(self, tx_data: Dict):
        """Returns right away, with no response

        https://binance-chain.github.io/api-reference/node-rpc.html#broadcasttxasync

        """
        return self._request_session("broadcast_tx_async", params=tx_data)

    def _broadcast_tx_commit(self, tx_data: Dict):
        """CONTRACT: only returns error if mempool.CheckTx() errs or if we timeout waiting for tx to commit.

        https://binance-chain.github.io/api-reference/node-rpc.html#broadcasttxcommit

        """
        return self._request_session("broadcast_tx_commit", params=tx_data)

    def _broadcast_tx_sync(self, tx_data: Dict):
        """Returns with the response from CheckTx.

        https://binance-chain.github.io/api-reference/node-rpc.html#broadcasttxsync

        """
        return self._request_session("broadcast_tx_sync", params=tx_data)

    def get_consensus_params(self, height: Optional[int] = None):
        """Get the consensus parameters at the given block height. If no height is provided, it will fetch the
        current consensus params.

        https://binance-chain.github.io/api-reference/node-rpc.html#consensusparams

        height: int

        """
        data = {
            'height': str(height) if height else None
        }

        return self._request('consensus_params', data=data)

    def get_tx(self, tx_hash: str, prove: Optional[bool] = None):
        """Tx allows you to query the transaction results. nil could mean the transaction is in the mempool,
        invalidated, or was not sent in the first place.

        https://binance-chain.github.io/api-reference/node-rpc.html#tx

        tx_hash	string	""	true	Query
        prove	bool	false	false	Include proofs of the transactions inclusion in the block

        """

        data = {
            'hash': tx_hash
        }
        if prove:
            data['prove'] = str(prove)

        return self._request('tx', data=data)

    def tx_search(self, query: str, prove: Optional[bool] = None,
                  page: Optional[int] = None, limit: Optional[int] = None):
        """TxSearch allows you to query for multiple transactions results. It returns a list of transactions
        (maximum ?per_page entries) and the total count.

        https://binance-chain.github.io/api-reference/node-rpc.html#txsearch

        query	string	""	true	Query
        prove	bool	false	false	Include proofs of the transactions inclusion in the block
        page	int	1	false	Page number (1-based)
        per_page	int	30	false	Number of entries per page (max: 100)

        """

        data = {
            'query': query
        }
        if prove:
            data['prove'] = str(prove)
        if page:
            data['page'] = str(page)
        if limit:
            data['limit'] = str(limit)

        return self._request('tx_search', data=data)


class AsyncHttpRpcClient(BaseHttpRpcClient):

    DEFAULT_TIMEOUT = 10

    @classmethod
    async def create(cls, endpoint_url):

        return AsyncHttpRpcClient(endpoint_url)

    def _init_session(self, **kwargs):

        loop = kwargs.get('loop', asyncio.get_event_loop())
        session = aiohttp.ClientSession(
            loop=loop,
            headers=self._get_headers()
        )
        return session

    async def _request(self, path, **kwargs):

        rpc_request = self._get_rpc_request(path, **kwargs)

        response = await self.session.post(self._endpoint_url, data=rpc_request.encode(), headers=self._get_headers())
        return await self._handle_response(response)

    async def _request_session(self, path, params=None):

        kwargs = {
            'params': params,
            'headers': self._get_headers()
        }

        response = await self.session.get(f"{self._endpoint_url}/{path}", **kwargs)

        return await self._handle_session_response(response)

    async def _handle_response(self, response):
        """Internal helper for handling API responses from the Binance server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """

        try:
            res = await response.json()

            if 'error' in res and res['error']:
                raise BinanceChainRPCException(response)

            # by default return full response
            # if it's a normal response we have a data attribute, return that
            if 'result' in res:
                res = res['result']
            return res
        except ValueError:
            raise BinanceChainRequestException('Invalid Response: %s' % response.text)

    async def _handle_session_response(self, response):
        """Internal helper for handling API responses from the Binance server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        if not str(response.status).startswith('2'):
            raise BinanceChainRPCException(response)
        try:
            res = await response.json()

            if 'code' in res and res['code'] != "200000":
                raise BinanceChainRPCException(response)

            if 'success' in res and not res['success']:
                raise BinanceChainRPCException(response)

            # by default return full response
            # if it's a normal response we have a data attribute, return that
            if 'result' in res:
                res = res['result']
            return res
        except ValueError:
            raise BinanceChainRequestException('Invalid Response: %s' % await response.text())

    async def get_path_list(self):
        res = await self.client.session.get(self._endpoint_url)
        return await res.text()
    get_path_list.__doc__ = HttpRpcClient.get_path_list.__doc__

    async def get_abci_info(self):
        return await self._request('abci_info')
    get_abci_info.__doc__ = HttpRpcClient.get_abci_info.__doc__

    async def get_consensus_state(self):
        return await self._request('consensus_state')
    get_consensus_state.__doc__ = HttpRpcClient.get_consensus_state.__doc__

    async def dump_consensus_state(self):
        return await self._request('dump_consensus_state')
    dump_consensus_state.__doc__ = HttpRpcClient.dump_consensus_state.__doc__

    async def get_genesis(self):
        return await self._request('genesis')
    get_genesis.__doc__ = HttpRpcClient.get_genesis.__doc__

    async def get_net_info(self):
        return await self._request('net_info')
    get_net_info.__doc__ = HttpRpcClient.get_net_info.__doc__

    async def get_num_unconfirmed_txs(self):
        return await self._request('num_unconfirmed_txs')
    get_num_unconfirmed_txs.__doc__ = HttpRpcClient.get_num_unconfirmed_txs.__doc__

    async def get_status(self):
        return await self._request('status')
    get_status.__doc__ = HttpRpcClient.get_status.__doc__

    async def get_health(self):
        return await self._request('health')
    get_health.__doc__ = HttpRpcClient.get_health.__doc__

    async def get_unconfirmed_txs(self):
        return await self._request('unconfirmed_txs')
    get_unconfirmed_txs.__doc__ = HttpRpcClient.get_unconfirmed_txs.__doc__

    async def get_validators(self):
        return await self._request('validators')
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

        return await self._request('abci_query', data=data)
    abci_query.__doc__ = HttpRpcClient.abci_query.__doc__

    async def get_block(self, height: Optional[int] = None):
        data = {
            'height': str(height) if height else None
        }
        return await self._request('block', data=data)
    get_block.__doc__ = HttpRpcClient.get_block.__doc__

    async def get_block_result(self, height: int):
        data = {
            'height': str(height)
        }
        return await self._request('block_result', data=data)
    get_block_result.__doc__ = HttpRpcClient.get_block_result.__doc__

    async def get_block_commit(self, height: int):
        data = {
            'height': str(height)
        }
        return await self._request('commit', data=data)
    get_block_commit.__doc__ = HttpRpcClient.get_block_commit.__doc__

    async def get_blockchain_info(self, min_height: int, max_height: int):
        assert max_height > min_height

        data = {
            'minHeight': str(min_height),
            'maxHeight': str(max_height)
        }

        return await self._request('blockchain', data=data)
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
        """Returns right away, with no response

        https://binance-chain.github.io/api-reference/node-rpc.html#broadcasttxasync

        """
        return await self._request_session('broadcast_tx_async', params=tx_data)
    _broadcast_tx_async.__doc__ = HttpRpcClient._broadcast_tx_async.__doc__

    async def _broadcast_tx_commit(self, tx_data: Dict):
        return await self._request_session('broadcast_tx_commit', params=tx_data)
    _broadcast_tx_commit.__doc__ = HttpRpcClient._broadcast_tx_commit.__doc__

    async def _broadcast_tx_sync(self, tx_data: Dict):
        return await self._request_session('broadcast_tx_sync', params=tx_data)
    _broadcast_tx_sync.__doc__ = HttpRpcClient._broadcast_tx_sync.__doc__

    async def get_consensus_params(self, height: Optional[int] = None):
        data = {
            'height': str(height) if height else None
        }

        return await self._request('consensus_params', data=data)
    get_consensus_params.__doc__ = HttpRpcClient.get_consensus_params.__doc__

    async def get_tx(self, tx_hash: str, prove: Optional[bool] = None):
        data = {
            'hash': tx_hash
        }
        if prove:
            data['prove'] = str(prove)

        return await self._request('tx', data=data)
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

        return await self._request('tx_search', data=data)
    tx_search.__doc__ = HttpRpcClient.tx_search.__doc__
