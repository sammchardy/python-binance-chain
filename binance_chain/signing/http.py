from typing import Optional, Dict

import asyncio
import aiohttp
import requests

import binance_chain.messages
from binance_chain.exceptions import (
    BinanceChainAPIException, BinanceChainRequestException,
    BinanceChainSigningAuthenticationException
)


class BaseApiSigningClient:

    def __init__(self, endpoint: str, username: str, password: str, requests_params: Optional[Dict] = None):
        """Binance Chain Signing API Client constructor

        :param endpoint: URL of signing service
        :param username: username for auth
        :param password: password for auth
        :param requests_params:

        """

        self._token = None
        self._endpoint = endpoint
        self._username = username
        self._password = password
        self._headers = {
            'Accept': 'application/json',
            'User-Agent': 'python-binance-chain',
        }
        self._requests_params = requests_params
        self.session = self._init_session()

    def _init_session(self):

        session = requests.session()
        session.headers.update(self._headers)
        return session

    def _create_uri(self, path):
        return f'{self._endpoint}/api/{path}'

    def authenticate(self):
        raise NotImplementedError()

    def _get_request_kwargs(self, method, **kwargs):

        # set default requests timeout
        kwargs['timeout'] = 10

        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)

        if self._token:
            kwargs['headers'] = {
                'Authorization': f'Bearer {self._token}'
            }

        return kwargs


class HttpApiSigningClient(BaseApiSigningClient):

    def __init__(self, endpoint: str, username: str, password: str, requests_params: Optional[Dict] = None):
        """Binance Chain Signing API Client constructor

        :param endpoint: URL of signing service
        :param username: username for auth
        :param password: password for auth
        :param requests_params:

        """

        super().__init__(endpoint, username, password, requests_params)

        self.authenticate()

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

            if 'message' in res:
                raise BinanceChainAPIException(response, response.status_code)

            return res
        except ValueError:
            raise BinanceChainRequestException('Invalid Response: %s' % response.text)

    def _get(self, path, **kwargs):
        return self._request('get', path, **kwargs)

    def _post(self, path, **kwargs):
        return self._request('post', path, **kwargs)

    def authenticate(self):
        data = {
            "username": self._username,
            "password": self._password
        }
        res = self._post("auth/login", json=data)

        self._token = res.get('access_token')

        if not self._token:
            raise BinanceChainSigningAuthenticationException("Invalid username and password")

    def sign_order(self, msg: binance_chain.messages.NewOrderMsg, wallet_name: str):
        """Sign a message using a signing service

        :param msg: Type of NewOrderMsg
        :param wallet_name: Name of the wallet

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
            res = client.sign_order(new_order_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('order/sign', json=data)

    def broadcast_order(self, msg: binance_chain.messages.NewOrderMsg, wallet_name: str):
        """Sign and broadcast a message using a signing service

        :param msg: Type of NewOrderMsg
        :param wallet_name: Name of the wallet

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
            res = client.broadcast_order(new_order_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('order/broadcast', json=data)

    def sign_cancel_order(self, msg: binance_chain.messages.CancelOrderMsg, wallet_name: str):
        """Sign a message using a signing service

        :param msg: Type of NewOrderMsg
        :param wallet_name: Name of the wallet

        .. code:: python

            # cancel order example
            cancel_order_msg = CancelOrderMsg(
                order_id="09F8B32D33CBE2B546088620CBEBC1FF80F9BE001ACF42762B0BBFF0A729CE3",
                symbol='ANN-457_BNB',
            )
            res = client.sign_cancel_order(cancel_order_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('order/cancel/sign', json=data)

    def broadcast_cancel_order(self, msg: binance_chain.messages.CancelOrderMsg, wallet_name: str):
        """Sign and broadcast a message using a signing service

        :param msg: Type of NewOrderMsg
        :param wallet_name: Name of the wallet

        .. code:: python

            # cancel order example
            cancel_order_msg = CancelOrderMsg(
                order_id="09F8B32D33CBE2B546088620CBEBC1FF80F9BE001ACF42762B0BBFF0A729CE3",
                symbol='ANN-457_BNB',
            )
            res = client.broadcast_cancel_order(cancel_order_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('order/cancel/broadcast', json=data)

    def sign_transfer(self, msg: binance_chain.messages.TransferMsg, wallet_name: str):
        """Sign a message using a signing service

        :param msg: Type of TransferMsg
        :param wallet_name: Name of the wallet

        .. code:: python

            transfer_msg = TransferMsg(
                symbol='BNB',
                amount=1,
                to_address='<to address>'
            )
            res = client.sign_transfer(transfer_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('transfer/sign', json=data)

    def broadcast_transfer(self, msg: binance_chain.messages.TransferMsg, wallet_name: str):
        """Sign and broadcast a message using a signing service

        :param msg: Type of TransferMsg
        :param wallet_name: Name of the wallet

        .. code:: python

            transfer_msg = TransferMsg(
                symbol='BNB',
                amount=1,
                to_address='<to address>'
            )
            res = client.sign_transfer(transfer_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('transfer/broadcast', json=data)

    def sign_freeze(self, msg: binance_chain.messages.FreezeMsg, wallet_name: str):
        """Sign a message using a signing service

        :param msg: Type of FreezeMsg
        :param wallet_name: Name of the wallet

        .. code:: python

            freeze_msg = FreezeMsg(
                symbol='BNB',
                amount=Decimal(10)
            )
            res = client.sign_freeze(freeze_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('freeze/sign', json=data)

    def broadcast_freeze(self, msg: binance_chain.messages.FreezeMsg, wallet_name: str):
        """Sign and broadcast a message using a signing service

        :param msg: Type of FreezeMsg
        :param wallet_name: Name of the wallet

        .. code:: python

            freeze_msg = FreezeMsg(
                symbol='BNB',
                amount=Decimal(10)
            )
            res = client.sign_transfer(freeze_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('freeze/broadcast', json=data)

    def sign_unfreeze(self, msg: binance_chain.messages.UnFreezeMsg, wallet_name: str):
        """Sign a message using a signing service

        :param msg: Type of UnFreezeMsg
        :param wallet_name: Name of the wallet

        .. code:: python

            unfreeze_msg = UnFreezeMsg(
                symbol='BNB',
                amount=Decimal(10)
            )
            res = client.sign_unfreeze(unfreeze_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('unfreeze/sign', json=data)

    def broadcast_unfreeze(self, msg: binance_chain.messages.UnFreezeMsg, wallet_name: str):
        """Sign and broadcast a message using a signing service

        :param msg: Type of UnFreezeMsg
        :param wallet_name: Name of the wallet

        .. code:: python

            unfreeze_msg = UnFreezeMsg(
                symbol='BNB',
                amount=Decimal(10)
            )
            res = client.sign_unfreeze(unfreeze_msg, wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return self._post('unfreeze/broadcast', json=data)

    def wallet_resync(self, wallet_name: str):
        """Resynchronise the wallet to the chain

        :param wallet_name:

        .. code:: python

            res = client.wallet_resync(wallet_name='mywallet')

        :return: API Response

        """
        data = {
            'wallet_name': wallet_name
        }
        return self._post('wallet/resync', json=data)

    def wallet_info(self, wallet_name: Optional[str] = None):
        """Get wallet information for the currently authenticated user

        :param wallet_name: Optional- if not passed returns all walets

        .. code:: python

            # info about all wallets
            res_all = client.wallet_info()

            # info about particular wallets
            res_mywallet = client.wallet_info(wallet_name='mywallet')

        :return: API Response

        """
        req_path = 'wallet'
        if wallet_name:
            req_path = f'wallet/{wallet_name}'
        return self._get(req_path)


class AsyncHttpApiSigningClient(BaseApiSigningClient):

    def __init__(self, endpoint: str, username: str, password: str,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 requests_params: Optional[Dict] = None):

        super().__init__(endpoint, username, password, requests_params=requests_params)

        self._loop = loop

    @classmethod
    async def create(cls,
                     endpoint: str, username: str, password: str,
                     loop: Optional[asyncio.AbstractEventLoop] = None,
                     requests_params: Optional[Dict] = None):

        return AsyncHttpApiSigningClient(endpoint, username, password, requests_params=requests_params, loop=loop)

    def _init_session(self, **kwargs):

        loop = kwargs.get('loop', asyncio.get_event_loop())
        session = aiohttp.ClientSession(
            loop=loop,
            headers=self._headers
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

    async def authenticate(self):
        data = {
            "username": self._username,
            "password": self._password
        }
        res = await self._post("auth/login", json=data)

        self._token = res.get('access_token')

        if not self._token:
            raise BinanceChainSigningAuthenticationException("Invalid username and password")

    async def sign_order(self, msg: binance_chain.messages.NewOrderMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('order/sign', json=data)
    sign_order.__doc__ = HttpApiSigningClient.sign_order.__doc__

    async def broadcast_order(self, msg: binance_chain.messages.NewOrderMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('order/broadcast', json=data)
    broadcast_order.__doc__ = HttpApiSigningClient.broadcast_order.__doc__

    async def sign_cancel_order(self, msg: binance_chain.messages.CancelOrderMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('order/cancel/sign', json=data)
    sign_cancel_order.__doc__ = HttpApiSigningClient.sign_cancel_order.__doc__

    async def broadcast_cancel_order(self, msg: binance_chain.messages.CancelOrderMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('order/cancel/broadcast', json=data)
    broadcast_cancel_order.__doc__ = HttpApiSigningClient.broadcast_cancel_order.__doc__

    async def sign_transfer(self, msg: binance_chain.messages.TransferMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('transfer/sign', json=data)
    sign_transfer.__doc__ = HttpApiSigningClient.sign_transfer.__doc__

    async def broadcast_transfer(self, msg: binance_chain.messages.TransferMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('transfer/broadcast', json=data)
    broadcast_transfer.__doc__ = HttpApiSigningClient.broadcast_transfer.__doc__

    async def sign_freeze(self, msg: binance_chain.messages.FreezeMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('freeze/sign', json=data)
    sign_freeze.__doc__ = HttpApiSigningClient.sign_freeze.__doc__

    async def broadcast_freeze(self, msg: binance_chain.messages.FreezeMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('freeze/broadcast', json=data)
    broadcast_freeze.__doc__ = HttpApiSigningClient.broadcast_freeze.__doc__

    async def sign_unfreeze(self, msg: binance_chain.messages.UnFreezeMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('unfreeze/sign', json=data)
    sign_unfreeze.__doc__ = HttpApiSigningClient.sign_unfreeze.__doc__

    async def broadcast_unfreeze(self, msg: binance_chain.messages.UnFreezeMsg, wallet_name: str):
        data = {
            'msg': msg.to_sign_dict(),
            'wallet_name': wallet_name
        }
        return await self._post('unfreeze/broadcast', json=data)
    broadcast_unfreeze.__doc__ = HttpApiSigningClient.broadcast_unfreeze.__doc__

    async def wallet_resync(self, wallet_name: str):
        data = {
            'wallet_name': wallet_name
        }
        return await self._post('wallet/resync', json=data)
    wallet_resync.__doc__ = HttpApiSigningClient.wallet_resync.__doc__

    async def wallet_info(self, wallet_name: Optional[str] = None):
        req_path = 'wallet'
        if wallet_name:
            req_path = f'wallet/{wallet_name}'
        return await self._get(req_path)
    wallet_info.__doc__ = HttpApiSigningClient.wallet_info.__doc__
