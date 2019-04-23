import mock
import pytest

from binance_chain.signing.http import HttpApiSigningClient, AsyncHttpApiSigningClient


class TestHttpSigningClient:

    @mock.patch('binance_chain.signing.http.HttpApiSigningClient.authenticate')
    def test_initialise(self, _mocker):

        assert HttpApiSigningClient('https://binance-signing-service.com', 'sam', 'mypass')


class TestAsyncHttpSigningClient:

    @mock.patch('binance_chain.signing.http.AsyncHttpApiSigningClient.authenticate')
    @pytest.mark.asyncio
    async def test_initialise(self, _mocker, event_loop):

        assert await AsyncHttpApiSigningClient.create('https://binance-signing-service.com', 'sam', 'mypass')

