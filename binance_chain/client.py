import binascii
import json
import logging
from collections import OrderedDict
from enum import Enum
from typing import Optional, Dict, Union
from decimal import Decimal

import requests

from .wallet import Wallet
from .exceptions import (
    BinanceChainAPIException, BinanceChainRequestException
)
from .dex_pb2 import NewOrder, CancelOrder, TokenFreeze, TokenUnfreeze, StdTx, StdSignature
from .segwit_addr import decode_address
from .utils import encode_number, varint_encode


# An identifier for tools triggering broadcast transactions, set to zero if unwilling to disclose.
BROADCAST_SOURCE = 1


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


class TimeInForce(str, Enum):
    GOOD_TILL_EXPIRE = "GTE"
    IMMEDIATE_OR_CANCEL = "IOC"


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


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class PeerType(str, Enum):
    NODE = 'node'
    WEBSOCKET = 'ws'


class Signature:

    def __init__(self, msg, account, data=None, chain_id='Binance-Chain-Nile', memo=''):
        self._msg = msg
        self._account = account
        self._chain_id = chain_id
        self._data = data
        self._memo = memo
        self._source = BROADCAST_SOURCE

    def to_json(self):
        return json.dumps(OrderedDict([
            ('account_number', str(self._account['account_number'])),
            ('chain_id', self._chain_id),
            ('data', self._data),
            ('memo', self._memo),
            ('msgs', [self._msg.to_dict(self._account)]),
            ('sequence', str(self._account['sequence'])),
            ('source', str(self._source))
        ]), separators=(',', ':'), ensure_ascii=False)

    def to_bytes_json(self):
        return self.to_json().encode()

    def sign(self, wallet):
        # sign string
        json_bytes = self.to_bytes_json()

        signed = wallet.sign_message(json_bytes)
        return signed[-64:]


class Msg:

    AMINO_MESSAGE_TYPE = ""
    INCLUDE_AMINO_LENGTH_PREFIX = False

    def to_dict(self, account) -> Dict:
        return {}

    def to_protobuf(self, account):
        pass

    def to_amino(self, account):
        proto = self.to_protobuf(account)
        # wrap with type

        if type(proto) != bytes:
            proto = proto.SerializeToString()

        type_bytes = b""
        if self.AMINO_MESSAGE_TYPE:
            type_bytes = binascii.unhexlify(self.AMINO_MESSAGE_TYPE)
            varint_length = varint_encode(len(proto) + len(type_bytes))
        else:
            varint_length = varint_encode(len(proto))

        msg = b""
        if self.INCLUDE_AMINO_LENGTH_PREFIX:
            msg += varint_length
        msg += type_bytes + proto

        return msg


class NewOrderMsg(Msg):

    ORDER_SIDE_INT = {
        OrderSide.BUY: 1,
        OrderSide.SELL: 2
    }

    ORDER_TYPE_INT = {
        OrderType.MARKET: 1,
        OrderType.LIMIT: 2
    }

    TIME_IN_FORCE_INT = {
        TimeInForce.GOOD_TILL_EXPIRE: 1,
        TimeInForce.IMMEDIATE_OR_CANCEL: 3
    }

    AMINO_MESSAGE_TYPE = b"CE6DC043"

    def __init__(self, symbol: str, time_in_force: TimeInForce, order_type: OrderType, side: OrderSide,
                 price: Union[int, float, Decimal], quantity: Union[int, float, Decimal]):
        """NewOrder transaction creates a new order to buy and sell tokens on Binance DEX.

        :param symbol: symbol for trading pair in full name of the tokens e.g. 'ANN-457_BNB'
        :param time_in_force: TimeInForce type (GOOD_TILL_EXPIRE, IMMEDIATE_OR_CANCEL)
        :param order_type: OrderType (LIMIT, MARKET)
        :param side: OrderSide (BUY, SELL)
        :param price: price of the order e.g. Decimal(0.000396000) or 0.002384
        :param quantity: quantity of the order Decimal(12) or 12

        """
        self._symbol = symbol
        self._time_in_force = NewOrderMsg.TIME_IN_FORCE_INT[time_in_force]
        self._order_type = NewOrderMsg.ORDER_TYPE_INT[order_type]
        self._side = NewOrderMsg.ORDER_SIDE_INT[side]
        self._price = encode_number(price)
        self._quantity = encode_number(quantity)

    def to_dict(self, account) -> Dict:
        order_id = self._generate_order_id(account)
        return OrderedDict([
            ('id', order_id),
            ('ordertype', self._order_type),
            ('price', self._price),
            ('quantity', self._quantity),
            ('sender', account['address']),
            ('side', self._side),
            ('symbol', self._symbol),
            ('timeinforce', self._time_in_force),
        ])

    def to_protobuf(self, account) -> NewOrder:
        pb = NewOrder()
        account_code = decode_address(account['address'])
        pb.sender = account_code
        pb.id = self._generate_order_id(account)
        pb.symbol = self._symbol.encode()
        pb.timeinforce = self._time_in_force
        pb.ordertype = self._order_type
        pb.side = self._side
        pb.price = self._price
        pb.quantity = self._quantity
        return pb

    def _generate_order_id(self, account):
        account_code = decode_address(account['address'])
        order_id = f"{binascii.hexlify(account_code).decode().upper()}-{(account['sequence'] + 1)}"
        return order_id


class CancelOrderMsg(Msg):

    AMINO_MESSAGE_TYPE = b"166E681B"

    def __init__(self, symbol: str, order_id: str):
        """Cancel transactions cancel the outstanding (unfilled) orders from the Binance DEX. After cancel success,
        the locked quantity on the orders would return back to the address' balance and become free to use,
        i.e. transfer or send new orders.

        :param symbol: symbol for trading pair in full name of the tokens
        :param order_id: order id of the one to cancel
        """
        self._symbol = symbol
        self._order_id = order_id

    def to_dict(self, account):
        return OrderedDict([
            ('refid', self._order_id),
            ('sender', account['address']),
            ('symbol', self._symbol),
        ])

    def to_protobuf(self, account) -> CancelOrder:
        pb = CancelOrder()
        account_code = decode_address(account['address'])
        pb.sender = account_code
        pb.refid = self._order_id
        pb.symbol = self._symbol.encode()
        return pb


class FreezeMsg(Msg):

    AMINO_MESSAGE_TYPE = b"E774B32D"

    def __init__(self, symbol: str, amount: Union[int, float, Decimal]):
        """Freeze transaction moves the amount of the tokens into a frozen state,
        in which it cannot be used to transfer or send new orders.

        :param symbol: token symbol, in full name with "-" suffix
        :param amount: amount of token to freeze
        """
        self._symbol = symbol
        self._amount = encode_number(amount)

    def to_dict(self, account):
        return OrderedDict([
            ('amount', self._amount),
            ('from', account['address']),
            ('symbol', self._symbol),
        ])

    def to_protobuf(self, account) -> TokenFreeze:
        pb = TokenFreeze()
        account_code = decode_address(account['address'])
        setattr(pb, 'from', account_code)
        pb.symbol = self._symbol.encode()
        pb.amount = self._amount
        return pb


class UnFreezeMsg(Msg):

    AMINO_MESSAGE_TYPE = b"6515FF0D"

    def __init__(self, symbol: str, amount: Union[int, float, Decimal]):
        """Turn the amount of frozen tokens back to free state.

        :param symbol: token symbol, in full name with "-" suffix
        :param amount: amount of token to unfreeze
        """
        self._symbol = symbol
        self._amount = encode_number(amount)

    def to_dict(self, account):
        return OrderedDict([
            ('amount', self._amount),
            ('from', account['address']),
            ('symbol', self._symbol),
        ])

    def to_protobuf(self, account) -> TokenUnfreeze:
        pb = TokenUnfreeze()
        account_code = decode_address(account['address'])
        setattr(pb, 'from', account_code)
        pb.symbol = self._symbol.encode()
        pb.amount = self._amount
        return pb


class SignatureMsg(Msg):

    AMINO_MESSAGE_TYPE = None

    def __init__(self, signature: Signature, wallet: Wallet):
        self._signature = signature
        self._wallet = wallet

    def to_protobuf(self, account) -> NewOrder:
        pub_key_msg = PubKeyMsg(self._wallet)
        std_sig = StdSignature()
        std_sig.sequence = account['sequence']
        std_sig.account_number = account['account_number']
        std_sig.pub_key = pub_key_msg.to_amino(account)
        std_sig.signature = self._signature.sign(self._wallet)
        return std_sig


class StdTxMsg(Msg):

    AMINO_MESSAGE_TYPE = b"F0625DEE"
    INCLUDE_AMINO_LENGTH_PREFIX = True

    def __init__(self, msg, signature: SignatureMsg, data='', memo=''):
        self._msg = msg
        self._signature = signature
        self._data = data
        self._memo = memo
        self._source = BROADCAST_SOURCE

    def to_protobuf(self, account) -> NewOrder:
        stdtx = StdTx()
        stdtx.msgs.extend([self._msg.to_amino(account)])
        stdtx.signatures.extend([self._signature.to_amino(account)])
        stdtx.data = self._data.encode()
        stdtx.memo = self._memo
        stdtx.source = self._source
        return stdtx


class PubKeyMsg(Msg):

    AMINO_MESSAGE_TYPE = b"EB5AE987"

    def __init__(self, wallet: Wallet):
        self._public_key = wallet.public_key

    def to_protobuf(self, account):
        return self._public_key

    def to_amino(self, account):
        proto = self.to_protobuf(account)

        type_bytes = binascii.unhexlify(self.AMINO_MESSAGE_TYPE)

        varint_length = varint_encode(len(proto))

        msg = type_bytes + varint_length + proto

        return msg


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

    def broadcast_msg(self, msg: Msg, sync: bool = False):
        """Broadcast a message

        https://binance-chain.github.io/api-reference/dex-api/paths.html#apiv1broadcast

        :param msg: Type of NewOrderMsg, CancelOrderMsg, FreezeMsg, UnfreezeMsg
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
            res = client.broadcast_msg(new_order_msg, wallet)

            # cancel order example
            cancel_order_msg = CancelOrderMsg(
                order_id="09F8B32D33CBE2B546088620CBEBC1FF80F9BE001ACF42762B0BBFF0A729CE3",
                symbol='ANN-457_BNB',
            )
            res = client.broadcast_msg(cancel_order_msg, wallet)

        :return: API Response

        """

        # fetch account detail
        account = self.get_account(self._wallet.address)

        signature = Signature(msg, account)
        signature_msg = SignatureMsg(signature, self._wallet)

        std_tx = StdTxMsg(msg, signature_msg)
        logging.debug(f'std_tx_amino:{std_tx.to_amino(account)}')

        data = binascii.hexlify(std_tx.to_amino(account))
        logging.debug(f'data:{data}')

        req_path = 'broadcast'
        if sync:
            req_path += f'?sync=1'

        return self._post(req_path, data=data)

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
