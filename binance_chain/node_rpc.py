from typing import Optional

from jsonrpcclient.clients.http_client import HTTPClient
from jsonrpcclient.requests import Request

from .exceptions import BinanceChainRPCException, BinanceChainRequestException


class RpcClient:

    def __init__(self, endpoint_url):

        self.endpoint_url = endpoint_url


class HttpRpcClient(RpcClient):

    def __init__(self, endpoint_url):
        super().__init__(endpoint_url)

        self.client = HTTPClient(endpoint_url)

    def _request(self, path, **kwargs):

        # set default requests timeout
        kwargs['timeout'] = 10

        # # add our global requests params
        # if self._requests_params:
        #     kwargs.update(self._requests_params)

        kwargs['data'] = kwargs.get('data', None)
        kwargs['headers'] = kwargs.get('headers', None)

        # full_path = self._create_path(path)
        # uri = self._create_uri(full_path)

        rcp_request = Request(path)
        if kwargs['data']:
            rcp_request.update(params=kwargs['data'])
        response = self.client.send(rcp_request)

        return self._handle_response(response)

    @staticmethod
    def _handle_response(response):
        """Internal helper for handling API responses from the server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """

        try:
            res = response.raw.json()

            if 'error' in res and res['error']:
                raise BinanceChainRPCException(response)

            # by default return full response
            # if it's a normal response we have a data attribute, return that
            if 'result' in res:
                res = res['result']
            return res
        except ValueError:
            raise BinanceChainRequestException('Invalid Response: %s' % response.text)

    def get_path_list(self):
        return self._request('')

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

    def get_block(self, height: int):
        """Get block at a given height. If no height is provided, it will fetch the latest block.

        https://binance-chain.github.io/api-reference/node-rpc.html#block

        height	int64

        """

        data = {
            'height': str(height)
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

    def broadcast_tx_async(self, tx: str):
        """Returns right away, with no response

        https://binance-chain.github.io/api-reference/node-rpc.html#broadcasttxasync

        tx	str

        """

        data = {
            'tx': tx
        }

        return self._request('broadcast_tx_async', data=data)

    def broadcast_tx_commit(self, tx: str):
        """CONTRACT: only returns error if mempool.CheckTx() errs or if we timeout waiting for tx to commit.

        https://binance-chain.github.io/api-reference/node-rpc.html#broadcasttxcommit

        tx	str

        """

        data = {
            'tx': tx
        }

        return self._request('broadcast_tx_commit', data=data)

    def broadcast_tx_sync(self, tx: str):
        """Returns with the response from CheckTx.

        https://binance-chain.github.io/api-reference/node-rpc.html#broadcasttxsync

        tx	str

        """

        data = {
            'tx': tx
        }

        return self._request('broadcast_tx_sync', data=data)

    def get_consensus_params(self, height: Optional[int] = None):
        """Get the consensus parameters at the given block height. If no height is provided, it will fetch the
        current consensus params.

        https://binance-chain.github.io/api-reference/node-rpc.html#consensusparams

        height: int

        """

        data = None
        if height:
            data = {
                'height': str(height)
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


class WebsocketRpcClient(RpcClient):
    pass
