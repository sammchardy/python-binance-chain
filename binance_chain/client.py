from enum import Enum
from typing import Optional, Dict

import requests

from .exceptions import (
    BinanceChainAPIException, BinanceChainRequestException
)


class KlineInterval(str, Enum):
    ONE_MINUTE = '1m'
    THREE_MINUTES = '3m'
    FVE_MINUTES = '5m'
    FIFTEEN_MINUTES = '15m'
    THIRTY_MINUTES = '30m'
    ONE_HOUR = '1h'
    TWO_HOURS = '2h'
    FOUR_HOURS = '4h'
    SIX_HOURS = '6h'
    EIGHT_HOURS = '8h'
    TWELVE_HOURS = '12h'
    ONE_DAY = '1d'
    THREE_DAYS = '3d'
    ONE_WEEK = '1w'
    ONE_MONTH = '1M'


class OrderStatus(str, Enum):
    ACK = 'Ack'
    PARTIAL_FILL = 'PartialFill'
    IOC_NO_FILL = 'IocNoFill'
    FULLY_FILL = 'FullyFill'
    CANCELED = 'Canceled'
    EXPIRED = 'Expired'
    FAILED_BLOCKING = 'FailedBlocking'
    FAILED_MATCHING = 'FailedMatching'


class OrderSide(str, Enum):
    BUY = 'buy'
    SELL = 'sell'


class TransactionSide(str, Enum):
    RECEIVE = 'RECEIVE'
    SEND = 'SEND'


class TransactionType(str, Enum):
    NEW_ORDER = 'NEW_ORDER'
    ISSUE_TOKEN = 'ISSUE_TOKEN'
    BURN_TOKEN = 'BURN_TOKEN'
    LIST_TOKEN = 'LIST_TOKEN'
    CANCEL_ORDER = 'CANCEL_ORDER'
    FREEZE_TOKEN = 'FREEZE_TOKEN'
    UN_FREEZE_TOKEN = 'UN_FREEZE_TOKEN'
    TRANSFER = 'TRANSFER'
    PROPOSAL = 'PROPOSAL'
    VOTE = 'VOTE'


class PeerType(str, Enum):
    NODE = 'node'
    WEBSOCKET = 'ws'


class Wallet:

    def __init__(self, address, private_key):

        self._address = address
        self._private_key = private_key
        self._public_key, _ = privtopub(self._private_key.encode())

    @property
    def address(self):
        return self._address

    @property
    def private_key(self):
        return self._private_key

    @property
    def public_key(self):
        return self._public_key


class Client:

    TESTNET_API_URL = 'https://testnet-dex.binance.org'
    API_VERSION = 'v1'

    def __init__(self, api_url: Optional[str] = None, wallet: Optional[Wallet] = None,
                 requests_params: Optional[Dict] = None):
        """Binance Chain API Client constructor

        https://binance-chain.github.io/api-reference/dex-api/paths.html

        :param requests_params: (optional) Dictionary of requests params to use for all calls
        :type requests_params: dict.

        .. code:: python

            client = Client(api_key, api_secret

        """

        self.API_URL = api_url or self.TESTNET_API_URL

        self._wallet = wallet
        self._requests_params = requests_params
        self.session = self._init_session()

    def _init_session(self):

        session = requests.session()
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'python-binance-chain',
        }
        session.headers.update(headers)
        return session

    def _create_path(self, path):
        return '/api/{}/{}'.format(self.API_VERSION, path)

    def _create_uri(self, path):
        return '{}{}'.format(self.API_URL, path)

    def _request(self, method, path, **kwargs):

        # set default requests timeout
        kwargs['timeout'] = 10

        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)

        kwargs['data'] = kwargs.get('data', {})
        kwargs['headers'] = kwargs.get('headers', {})

        full_path = self._create_path(path)
        uri = self._create_uri(full_path)

        if kwargs['data'] and method == 'get':
            kwargs['params'] = kwargs['data']
            del(kwargs['data'])

        if method == 'post':
            kwargs['headers']['content-type'] = 'text/plain'

        response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response):
        """Internal helper for handling API responses from the server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """

        if not str(response.status_code).startswith('2'):
            raise BinanceChainAPIException(response)
        try:
            res = response.json()

            if 'code' in res and res['code'] != "200000":
                raise BinanceChainAPIException(response)

            if 'success' in res and not res['success']:
                raise BinanceChainAPIException(response)

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

        data = {
            'format': 'json'
        }

        return self._get(f"tx/{transaction_hash}?format=json", data=data)

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

    def get_broadcast(self, transaction: str):
        """Gets the order book depth data for a given pair symbol

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1broadcast

        :param symbol: required e.g NNB-0AD_BNB

        .. code:: python

            order_book = client.get_order_book('NNB-0AD_BNB')

        :return: API Response

        """
        # TODO: implement transactions
        # data = {
        #     'sync': sync
        #     'body': body
        # }
        # return self._post("broadcast", False, data=data)
        pass

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
            'interval': interval
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
            data['status'] = status
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
            data['side'] = side
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
            data['side'] = side
        if tx_asset is not None:
            data['txAsset'] = tx_asset
        if tx_type is not None:
            data['txType'] = tx_type
        if height is not None:
            data['blockHeight'] = height
        if offset is not None:
            data['offset'] = offset
        if limit is not None:
            data['limit'] = limit
        if start_time is not None:
            data['start'] = start_time
        if end_time is not None:
            data['end'] = end_time

        return self._get("transactions", data=data)
