import logging
from typing import Optional, Dict

import asyncio
import aiohttp
import requests

import binance_chain.messages
from binance_chain.environment import BinanceEnvironment
from binance_chain.constants import PeerType, KlineInterval, OrderSide, OrderStatus, TransactionSide, TransactionType
from binance_chain.exceptions import (
    BinanceChainAPIException, BinanceChainRequestException, BinanceChainBroadcastException
)


class BaseApiClient:

    API_VERSION = 'v1'

    def __init__(self, env: Optional[BinanceEnvironment] = None, requests_params: Optional[Dict] = None, **kwargs):
        """Binance Chain API Client constructor

        https://binance-chain.github.io/api-reference/dex-api/paths.html

        :param env: (optional) A BinanceEnvironment instance or None which will default to production env
        :param requests_params: (optional) Dictionary of requests params to use for all calls
        :type requests_params: dict.

        .. code:: python

            # get production env client
            prod_client = Client()

            # get testnet env client
            testnet_env = BinanceEnvironment.get_testnet_env()
            client = Client(testnet_env)

        """

        self._env = env or BinanceEnvironment.get_production_env()
        self._requests_params = requests_params
        self.session = self._init_session(**kwargs)

    def _init_session(self, **kwargs):

        session = requests.session()
        headers = self._get_headers()
        session.headers.update(headers)
        return session

    @property
    def env(self):
        return self._env

    def _create_uri(self, path):
        full_path = '/api/{}/{}'.format(self.API_VERSION, path)
        return '{}{}'.format(self._env.api_url, full_path)

    def _get_headers(self):
        return {
            'Accept': 'application/json',
            'User-Agent': 'python-binance-chain',
        }

    def _get_request_kwargs(self, method, **kwargs):

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


class HttpApiClient(BaseApiClient):

    def _request(self, method, path, **kwargs):

        uri = self._create_uri(path)

        kwargs = self._get_request_kwargs(method, **kwargs)

        response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response):
        """Internal helper for handling API responses from the server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """

        if not str(response.status_code).startswith('2'):
            raise BinanceChainAPIException(response, response.status_code)
        try:
            res = response.json()

            if 'code' in res and res['code'] != "200000":
                raise BinanceChainAPIException(response, response.status_code)

            if 'success' in res and not res['success']:
                raise BinanceChainAPIException(response, response.status_code)

            # by default return full response
            # if it's a normal response we have a data attribute, return that
            if 'data' in res:
                res = res['data']
            return res
        except ValueError:
            raise BinanceChainRequestException('Invalid Response: %s' % response.text)

    def _get(self, path, **kwargs):
        return self._request('get', path, **kwargs)

    def _post(self, path, **kwargs):
        return self._request('post', path, **kwargs)

    def _put(self, path, **kwargs):
        return self._request('put', path, **kwargs)

    def _delete(self, path, **kwargs):
        return self._request('delete', path, **kwargs)

    def get_time(self):
        """Get the server timestamp

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1time

        .. code:: python

            time = client.get_time()

        :return: API Response

        .. code-block:: python

            {
                "ap_time": "2019-02-24T09:23:35Z",
                "block_time": "2019-02-24T09:23:34Z"
            }

        """
        return self._get("time")

    def get_node_info(self):
        """Get node runtime information

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1node-info

        .. code:: python

            node_info = client.get_node_info()

        :return: API Response

        """
        return self._get("node-info")

    def get_validators(self):
        """Gets the list of validators used in consensus

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1validators

        .. code:: python

            validators = client.get_validators()

        :return: API Response

        """
        return self._get("validators")

    def get_peers(self, peer_type: Optional[PeerType] = None):
        """Gets the list of network peers

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1peers

        .. code:: python

            peers = client.get_peers()

        :return: API Response

        """
        peers = self._get("peers")
        if peer_type:
            peers = [p for p in peers if peer_type in p['capabilities']]

        return peers

    def get_node_peers(self):
        """Get a list of peers with Node RPC support

        :return:
        """
        return self.get_peers(peer_type=PeerType.NODE)

    def get_websocket_peers(self):
        """Get a list of peers with Websocket support

        :return:
        """
        return self.get_peers(peer_type=PeerType.WEBSOCKET)

    def get_account(self, address: str):
        """Gets account metadata for an address

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1accountaddress

        .. code:: python

            account = client.get_account('tbnb185tqzq3j6y7yep85lncaz9qeectjxqe5054cgn')

        :return: API Response

        """
        return self._get(f"account/{address}")

    def get_account_sequence(self, address: str):
        """Gets an account sequence for an address.

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1accountaddresssequence

        .. code:: python

            account_seq = client.get_account_sequence('tbnb185tqzq3j6y7yep85lncaz9qeectjxqe5054cgn')

        :return: API Response

        .. code-block:: python

        """
        return self._get(f"account/{address}/sequence")

    def get_transaction(self, transaction_hash: str):
        """Gets transaction metadata by transaction ID

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1txhash

        .. code:: python

            account_seq = client.get_transaction('E81BAB8E555819E4211D62E2E536B6D5812D3D91C105F998F5C6EB3AB8136482')

        :return: API Response

        """

        return self._get(f"tx/{transaction_hash}?format=json")

    def get_tokens(self):
        """Gets a list of tokens that have been issued

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1tokens

        .. code:: python

            tokens = client.get_tokens()

        :return: API Response

        """
        return self._get("tokens")

    def get_markets(self):
        """Gets the list of market pairs that have been listed

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1markets

        .. code:: python

            markets = client.get_markets()

        :return: API Response

        """
        return self._get("markets")

    def get_fees(self):
        """Gets the current trading fees settings

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1fees

        .. code:: python

            fees = client.get_fees()

        :return: API Response

        """
        return self._get("fees")

    def get_order_book(self, symbol: str):
        """Gets the order book depth data for a given pair symbol

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1depth

        :param symbol: required e.g NNB-0AD_BNB

        .. code:: python

            order_book = client.get_order_book('NNB-0AD_BNB')

        :return: API Response

        """
        data = {
            'symbol': symbol
        }
        return self._get("depth", data=data)

    def broadcast_msg(self, msg: binance_chain.messages.Msg, sync: bool = False):
        """Broadcast a message

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1broadcast

        :param msg: Type of NewOrderMsg, CancelOrderMsg, FreezeMsg, UnfreezeMsg
        :param sync: Synchronous broadcast (wait for DeliverTx)?

        .. code:: python

            # new order example
            # construct the message
            new_order_msg = NewOrderMsg(
                wallet=wallet,
                symbol="ANN-457_BNB",
                time_in_force=TimeInForce.GTE,
                order_type=OrderType.LIMIT,
                side=OrderSide.BUY,
                price=Decimal(0.000396000),
                quantity=Decimal(12)
            )
            # then broadcast it
            res = client.broadcast_msg(new_order_msg, sync=True)

            # cancel order example
            cancel_order_msg = CancelOrderMsg(
                wallet=wallet,
                order_id="09F8B32D33CBE2B546088620CBEBC1FF80F9BE001ACF42762B0BBFF0A729CE3",
                symbol='ANN-457_BNB',
            )
            res = client.broadcast_msg(cancel_order_msg, sync=True)

        :return: API Response

        """

        # fetch account detail
        # account = self.get_account(self.msg.wallet.address)

        if self._env != msg.wallet.env:
            raise BinanceChainBroadcastException("Wallet environment doesn't match HttpApiClient environment")

        msg.wallet.initialise_wallet()
        data = msg.to_hex_data()

        req_path = 'broadcast'
        if sync:
            req_path += f'?sync=1'

        res = self._post(req_path, data=data)
        msg.wallet.increment_account_sequence()
        return res

    def broadcast_hex_msg(self, hex_msg: str, sync: bool = False):
        """Broadcast a message in hex format

        This may have been generated internally or by a signing service

        It is up to the user to keep track of the account sequence when using this method

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1broadcast

        :param hex_msg: signed message string
        :param sync: Synchronous broadcast (wait for DeliverTx)?

        .. code:: python

            # new order example
            # construct the message
            new_order_msg = NewOrderMsg(
                symbol="ANN-457_BNB",
                time_in_force=TimeInForce.GTE,
                order_type=OrderType.LIMIT,
                side=OrderSide.BUY,
                price=Decimal(0.000396000),
                quantity=Decimal(12)
            )

            # then broadcast it
            res = client.broadcast_hex_msg(hex_msg=new_order_msg.to_hex_data(), sync=True)

            #

            # cancel order example
            cancel_order_msg = CancelOrderMsg(
                order_id="09F8B32D33CBE2B546088620CBEBC1FF80F9BE001ACF42762B0BBFF0A729CE3",
                symbol='ANN-457_BNB',
            )
            res = client.broadcast_msg(cancel_order_msg.to_hex_data(), sync=True)

        :return: API Response

        """
        req_path = 'broadcast'
        if sync:
            req_path += f'?sync=1'

        res = self._post(req_path, data=hex_msg)
        return res

    def get_klines(self, symbol: str, interval: KlineInterval, limit: Optional[int] = 300,
                   start_time: Optional[int] = None, end_time: Optional[int] = None):
        """Gets candlestick/kline bars for a symbol. Bars are uniquely identified by their open time

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1klines

        :param symbol: required e.g NNB-0AD_BNB
        :param interval: required e.g 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        :param limit:
        :param start_time:
        :param end_time:

        .. code:: python

            klines = client.get_klines('NNB-0AD_BNB', KlineInterval.ONE_DAY)

        :return: API Response

        """
        data = {
            'symbol': symbol,
            'interval': interval.value
        }
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['startTime'] = start_time
        if end_time is not None:
            data['endTime'] = end_time

        return self._get("klines", data=data)

    def get_closed_orders(
        self, address: str, symbol: Optional[str] = None, status: Optional[OrderStatus] = None,
        side: Optional[OrderSide] = None, offset: Optional[int] = 0, limit: Optional[int] = 500,
        start_time: Optional[int] = None, end_time: Optional[int] = None, total: Optional[int] = 0
    ):
        """Gets closed (filled and cancelled) orders for a given address

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1ordersclosed

        :param address: required
        :param symbol: e.g NNB-0AD_BNB
        :param status: order status type
        :param side: order side. 1 for buy and 2 for sell.
        :param offset: start with 0; default 0.
        :param limit: default 500; max 1000.
        :param start_time:
        :param end_time:
        :param total: total number required, 0 for not required and 1 for required, default not required, return total=-1

        .. code:: python

            orders = client.get_closed_orders('tbnb185tqzq3j6y7yep85lncaz9qeectjxqe5054cgn')

        :return: API Response

        """
        data = {
            'address': address
        }
        if symbol is not None:
            data['symbol'] = symbol
        if status is not None:
            data['status'] = status.value
        if side is not None:
            data['side'] = side.value
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['start'] = start_time
        if end_time is not None:
            data['end'] = end_time
        if total is not None:
            data['total'] = total

        return self._get("orders/closed", data=data)

    def get_open_orders(
        self, address: str, symbol: Optional[str] = None, offset: Optional[int] = 0, limit: Optional[int] = 500,
        total: Optional[int] = 0
    ):
        """Gets open orders for a given address

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1ordersopen

        :param address: required
        :param symbol: e.g NNB-0AD_BNB
        :param offset: start with 0; default 0.
        :param limit: default 500; max 1000.
        :param total: total number required, 0 for not required and 1 for required, default not required, return total=-1

        .. code:: python

            orders = client.get_open_orders('tbnb185tqzq3j6y7yep85lncaz9qeectjxqe5054cgn')

        :return: API Response

        """
        data = {
            'address': address
        }
        if symbol is not None:
            data['symbol'] = symbol
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if total is not None:
            data['total'] = total

        return self._get("orders/open", data=data)

    def get_order(self, order_id: str):
        """Gets metadata for an individual order by its ID

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1ordersid

        :param order_id: required

        .. code:: python

            orders = client.get_order('')

        :return: API Response

        """

        return self._get(f"orders/{order_id}")

    def get_ticker(self, symbol: str):
        """Gets 24 hour price change statistics for a market pair symbol

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1ticker24hr

        :param symbol: required

        .. code:: python

            ticker = client.get_ticker('NNB-0AD_BNB')

        :return: API Response

        """
        data = {
            'symbol': symbol
        }

        return self._get("ticker/24hr", data=data)

    def get_trades(
        self, address: Optional[str] = None, symbol: Optional[str] = None,
        side: Optional[OrderSide] = None, quote_asset: Optional[str] = None, buyer_order_id: Optional[str] = None,
        seller_order_id: Optional[str] = None, height: Optional[str] = None, offset: Optional[int] = 0,
        limit: Optional[int] = 500, start_time: Optional[int] = None, end_time: Optional[int] = None,
        total: Optional[int] = 0
    ):
        """Gets a list of historical trades

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1trades

        :param address:
        :param symbol:
        :param side:
        :param quote_asset:
        :param buyer_order_id:
        :param seller_order_id:
        :param height:
        :param offset:
        :param limit:
        :param start_time:
        :param end_time:
        :param total:

        .. code:: python

            trades = client.get_trades('')

        :return: API Response

        """
        data = {}
        if address is not None:
            data['address'] = address
        if symbol is not None:
            data['symbol'] = symbol
        if side is not None:
            data['side'] = side.value
        if quote_asset is not None:
            data['quoteAsset'] = quote_asset
        if buyer_order_id is not None:
            data['buyerOrderId'] = buyer_order_id
        if seller_order_id is not None:
            data['sellerOrderId'] = seller_order_id
        if height is not None:
            data['height'] = height
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['start'] = start_time
        if end_time is not None:
            data['end'] = end_time
        if total is not None:
            data['total'] = total

        return self._get("trades", data=data)

    def get_transactions(
        self, address: str, symbol: Optional[str] = None,
        side: Optional[TransactionSide] = None, tx_asset: Optional[str] = None,
        tx_type: Optional[TransactionType] = None, height: Optional[str] = None, offset: Optional[int] = 0,
        limit: Optional[int] = 500, start_time: Optional[int] = None, end_time: Optional[int] = None
    ):
        """Gets a list of transactions

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1transactions

        :param address:
        :param symbol:
        :param side:
        :param tx_asset:
        :param tx_type:
        :param height:
        :param offset:
        :param limit:
        :param start_time:
        :param end_time:

        .. code:: python

            transactions = client.get_transactions('')

        :return: API Response

        """
        data = {
            'address': address
        }
        if symbol is not None:
            data['symbol'] = symbol
        if side is not None:
            data['side'] = side.value
        if tx_asset is not None:
            data['txAsset'] = tx_asset
        if tx_type is not None:
            data['txType'] = tx_type.value
        if height is not None:
            data['blockHeight'] = height
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['startTime'] = start_time
        if end_time is not None:
            data['endTime'] = end_time

        return self._get("transactions", data=data)

    def get_block_exchange_fee(
        self, address: Optional[str] = None, offset: Optional[int] = 0, total: Optional[int] = 0,
        limit: Optional[int] = 500, start_time: Optional[int] = None, end_time: Optional[int] = None
    ):
        """Trading fee of the address grouped by block

        https://docs.binance.org/api-reference/dex-api/paths.html#apiv1block-exchange-fee

        :param address:
        :param offset:
        :param limit:
        :param start_time:
        :param end_time:
        :param total:

        .. code:: python

            transactions = client.get_transactions('')

        :return: API Response

        """
        data = {}
        if address is not None:
            data['address'] = address
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['start'] = start_time
        if end_time is not None:
            data['end'] = end_time
        if total is not None:
            data['total'] = total

        return self._get("block-exchange-fee", data=data)


class AsyncHttpApiClient(BaseApiClient):

    @classmethod
    async def create(cls,
                     loop: Optional[asyncio.AbstractEventLoop] = None,
                     env: Optional[BinanceEnvironment] = None,
                     requests_params: Optional[Dict] = None):

        return AsyncHttpApiClient(env, requests_params, loop=loop)

    def _init_session(self, **kwargs):

        loop = kwargs.get('loop', asyncio.get_event_loop())
        session = aiohttp.ClientSession(
            loop=loop,
            headers=self._get_headers()
        )
        return session

    async def _request(self, method, path, **kwargs):

        uri = self._create_uri(path)

        kwargs = self._get_request_kwargs(method, **kwargs)

        async with getattr(self.session, method)(uri, **kwargs) as response:
            return await self._handle_response(response)

    async def _handle_response(self, response):
        """Internal helper for handling API responses from the Binance server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        if not str(response.status).startswith('2'):
            raise BinanceChainAPIException(response, response.status)
        try:
            res = await response.json()

            if 'code' in res and res['code'] != "200000":
                raise BinanceChainAPIException(response, response.status)

            if 'success' in res and not res['success']:
                raise BinanceChainAPIException(response, response.status)

            # by default return full response
            # if it's a normal response we have a data attribute, return that
            if 'data' in res:
                res = res['data']
            return res
        except ValueError:
            raise BinanceChainRequestException('Invalid Response: %s' % await response.text())

    async def _get(self, path, **kwargs):
        return await self._request('get', path, **kwargs)

    async def _post(self, path, **kwargs):
        return await self._request('post', path, **kwargs)

    async def _put(self, path, **kwargs):
        return await self._request('put', path, **kwargs)

    async def _delete(self, path, **kwargs):
        return await self._request('delete', path, **kwargs)

    async def get_time(self):
        return await self._get("time")
    get_time.__doc__ = HttpApiClient.get_time.__doc__

    async def get_node_info(self):
        return await self._get("node-info")
    get_node_info.__doc__ = HttpApiClient.get_node_info.__doc__

    async def get_validators(self):
        return await self._get("validators")
    get_validators.__doc__ = HttpApiClient.get_validators.__doc__

    async def get_peers(self, peer_type: Optional[PeerType] = None):
        peers = await self._get("peers")
        if peer_type:
            peers = [p for p in peers if peer_type in p['capabilities']]

        return peers
    get_peers.__doc__ = HttpApiClient.get_peers.__doc__

    async def get_node_peers(self):
        return await self.get_peers(peer_type=PeerType.NODE)
    get_node_peers.__doc__ = HttpApiClient.get_node_peers.__doc__

    async def get_websocket_peers(self):
        return await self.get_peers(peer_type=PeerType.WEBSOCKET)
    get_websocket_peers.__doc__ = HttpApiClient.get_websocket_peers.__doc__

    async def get_account(self, address: str):
        return await self._get(f"account/{address}")
    get_account.__doc__ = HttpApiClient.get_account.__doc__

    async def get_account_sequence(self, address: str):
        return await self._get(f"account/{address}/sequence")
    get_account_sequence.__doc__ = HttpApiClient.get_account_sequence.__doc__

    async def get_transaction(self, transaction_hash: str):
        return await self._get(f"tx/{transaction_hash}?format=json")
    get_transaction.__doc__ = HttpApiClient.get_transaction.__doc__

    async def get_tokens(self):
        return await self._get("tokens")
    get_tokens.__doc__ = HttpApiClient.get_tokens.__doc__

    async def get_markets(self):
        return await self._get("markets")
    get_markets.__doc__ = HttpApiClient.get_markets.__doc__

    async def get_fees(self):
        return await self._get("fees")
    get_fees.__doc__ = HttpApiClient.get_fees.__doc__

    async def get_order_book(self, symbol: str):
        data = {
            'symbol': symbol
        }
        return await self._get("depth", data=data)
    get_order_book.__doc__ = HttpApiClient.get_order_book.__doc__

    async def broadcast_msg(self, msg: binance_chain.messages.Msg, sync: bool = False):
        # fetch account detail
        # account = self.get_account(self.msg.wallet.address)

        if self._env != msg.wallet.env:
            raise BinanceChainBroadcastException("Wallet environment doesn't match HttpApiClient environment")

        msg.wallet.initialise_wallet()
        data = msg.to_hex_data()

        logging.debug(f'data:{data}')

        req_path = 'broadcast'
        if sync:
            req_path += f'?sync=1'

        res = await self._post(req_path, data=data)
        msg.wallet.increment_account_sequence()
        return res
    broadcast_msg.__doc__ = HttpApiClient.broadcast_msg.__doc__

    async def broadcast_hex_msg(self, hex_msg: str, sync: bool = False):
        req_path = 'broadcast'
        if sync:
            req_path += f'?sync=1'

        res = await self._post(req_path, data=hex_msg)
        return res
    broadcast_msg.__doc__ = HttpApiClient.broadcast_msg.__doc__

    async def get_klines(self, symbol: str, interval: KlineInterval, limit: Optional[int] = 300,
                         start_time: Optional[int] = None, end_time: Optional[int] = None):
        data = {
            'symbol': symbol,
            'interval': interval.value
        }
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['startTime'] = start_time
        if end_time is not None:
            data['endTime'] = end_time

        return await self._get("klines", data=data)
    get_klines.__doc__ = HttpApiClient.get_klines.__doc__

    async def get_closed_orders(
        self, address: str, symbol: Optional[str] = None, status: Optional[OrderStatus] = None,
        side: Optional[OrderSide] = None, offset: Optional[int] = 0, limit: Optional[int] = 500,
        start_time: Optional[int] = None, end_time: Optional[int] = None, total: Optional[int] = 0
    ):
        data = {
            'address': address
        }
        if symbol is not None:
            data['symbol'] = symbol
        if status is not None:
            data['status'] = status.value
        if side is not None:
            data['side'] = side
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['start'] = start_time
        if end_time is not None:
            data['end'] = end_time
        if total is not None:
            data['total'] = total

        return await self._get("orders/closed", data=data)
    get_closed_orders.__doc__ = HttpApiClient.get_closed_orders.__doc__

    async def get_open_orders(
        self, address: str, symbol: Optional[str] = None, offset: Optional[int] = 0, limit: Optional[int] = 500,
        total: Optional[int] = 0
    ):
        data = {
            'address': address
        }
        if symbol is not None:
            data['symbol'] = symbol
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if total is not None:
            data['total'] = total

        return await self._get("orders/open", data=data)
    get_open_orders.__doc__ = HttpApiClient.get_open_orders.__doc__

    async def get_order(self, order_id: str):
        return await self._get(f"orders/{order_id}")
    get_order.__doc__ = HttpApiClient.get_order.__doc__

    async def get_ticker(self, symbol: str):
        data = {
            'symbol': symbol
        }

        return await self._get("ticker/24hr", data=data)
    get_ticker.__doc__ = HttpApiClient.get_ticker.__doc__

    async def get_trades(
        self, address: Optional[str] = None, symbol: Optional[str] = None,
        side: Optional[OrderSide] = None, quote_asset: Optional[str] = None, buyer_order_id: Optional[str] = None,
        seller_order_id: Optional[str] = None, height: Optional[str] = None, offset: Optional[int] = 0,
        limit: Optional[int] = 500, start_time: Optional[int] = None, end_time: Optional[int] = None,
        total: Optional[int] = 0
    ):
        data = {}
        if address is not None:
            data['address'] = address
        if symbol is not None:
            data['symbol'] = symbol
        if side is not None:
            data['side'] = side.value
        if quote_asset is not None:
            data['quoteAsset'] = quote_asset
        if buyer_order_id is not None:
            data['buyerOrderId'] = buyer_order_id
        if seller_order_id is not None:
            data['sellerOrderId'] = seller_order_id
        if height is not None:
            data['height'] = height
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['start'] = start_time
        if end_time is not None:
            data['end'] = end_time
        if total is not None:
            data['total'] = total

        return await self._get("trades", data=data)
    get_trades.__doc__ = HttpApiClient.get_trades.__doc__

    async def get_transactions(
        self, address: str, symbol: Optional[str] = None,
        side: Optional[TransactionSide] = None, tx_asset: Optional[str] = None,
        tx_type: Optional[TransactionType] = None, height: Optional[str] = None, offset: Optional[int] = 0,
        limit: Optional[int] = 500, start_time: Optional[int] = None, end_time: Optional[int] = None
    ):
        data = {
            'address': address
        }
        if symbol is not None:
            data['symbol'] = symbol
        if side is not None:
            data['side'] = side.value
        if tx_asset is not None:
            data['txAsset'] = tx_asset
        if tx_type is not None:
            data['txType'] = tx_type.value
        if height is not None:
            data['blockHeight'] = height
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['startTime'] = start_time
        if end_time is not None:
            data['endTime'] = end_time

        return await self._get("transactions", data=data)
    get_transactions.__doc__ = HttpApiClient.get_transactions.__doc__

    async def get_block_exchange_fee(
        self, address: Optional[str] = None, offset: Optional[int] = 0, total: Optional[int] = 0,
        limit: Optional[int] = 500, start_time: Optional[int] = None, end_time: Optional[int] = None
    ):
        data = {}
        if address is not None:
            data['address'] = address
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['start'] = start_time
        if end_time is not None:
            data['end'] = end_time
        if total is not None:
            data['total'] = total

        return await self._get("block-exchange-fee", data=data)
    get_block_exchange_fee.__doc__ = HttpApiClient.get_block_exchange_fee.__doc__
