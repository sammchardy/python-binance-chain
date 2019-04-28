=======================================
Welcome to python-binance-chain v0.1.17
=======================================

.. image:: https://img.shields.io/pypi/v/python-binance-chain.svg
    :target: https://pypi.python.org/pypi/python-binance-chain

.. image:: https://img.shields.io/pypi/l/python-binance-chain.svg
    :target: https://pypi.python.org/pypi/python-binance-chain

.. image:: https://img.shields.io/travis/sammchardy/python-binance-chain.svg
    :target: https://travis-ci.org/sammchardy/python-binance-chain

.. image:: https://img.shields.io/coveralls/sammchardy/python-binance-chain.svg
    :target: https://coveralls.io/github/sammchardy/python-binance-chain

.. image:: https://img.shields.io/pypi/wheel/python-binance-chain.svg
    :target: https://pypi.python.org/pypi/python-binance-chain

.. image:: https://img.shields.io/pypi/pyversions/python-binance-chain.svg
    :target: https://pypi.python.org/pypi/python-binance-chain

This is an unofficial Python3 wrapper for the `Binance Chain API <https://binance-chain.github.io/api-reference/dex-api/paths.html>`_. I am in no way affiliated with Binance, use at your own risk.


PyPi
  https://pypi.python.org/pypi/python-binance-chain

Source code
  https://github.com/sammchardy/python-binance-chain


Features
--------

- Support for Testnet and Production `environments <#environments>`_, along with user defined environment
- HTTP API `sync <#quick-start>`_ and `async <#async-http-client>`_ implementations
- `Async Websockets <#websockets>`_ with auto-reconnection and backoff retry algorithm
- HTTP RPC Node `sync <#node-rpc-http>`_ and `async <#node-rpc-http-async>`_ implementations
- `Async Node RPC Websockets <#node-rpc-websockets>`_ with auto-reconnection and backoff retry algorithm
- `Wallet <#wallet>`_ creation from private key or mnemonic or new wallet with random mnemonic
- Wallet handling account sequence for transactions
- Broadcast Transactions over `HTTP <#broadcast-messages-on-httpapiclient>`_ and `RPC <#node-rpc-http>`_ with helper classes for limit buy and sell
- `Sign transactions <#sign-transaction>`_ and use the signed message how you want
- `Ledger hardware wallet <#ledger>`_ device (Ledger Blue, Nano S & Nano X) support for signing messages
- Async `Depth Cache <#depth-cache>`_ to keep a copy of the order book locally
- `Signing Service Support <#signing-service>`_ for `binance-chain-signing-service <https://github.com/sammchardy/binance-chain-signing-service>`_
- Support for proxies and to override `Requests and AioHTTP settings <requests-and-aiohttp-settings>`_
- `UltraJson <https://github.com/esnme/ultrajson>`_ the ultra fast JSON parsing library for efficient message handling
- Strong Python3 typing to reduce errors
- pytest `test suite <#running-tests>`_
- Response exception handling

Read the `Changelog <https://python-binance-chain.readthedocs.io/en/latest/changelog.html>`_


Recommended Resources
---------------------

- `Binance Chain Forum <https://community.binance.org/>`_
- `Binance Chain Telegram <https://t.me/BinanceDEXchange>`_
- `Binance Chain API <https://binance-chain.github.io/>`_
- `Tendermint Docs <https://tendermint.com/docs/>`_
- `Get Testnet Funds <https://www.binance.vision/tutorials/binance-dex-funding-your-testnet-account>`_


Quick Start
-----------

.. code:: bash

    pip install python-binance-chain

If having issues with secp256k1 check the `Installation instructions for the sec256k1-py library <https://github.com/ludbb/secp256k1-py#installation>`_

If using the production server there is no need to pass the environment variable.

.. code:: python

    from binance_chain.http import HttpApiClient
    from binance_chain.constants import KlineInterval
    from binance_chain.environment import BinanceEnvironment

    # initialise with Testnet environment
    testnet_env = BinanceEnvironment.get_testnet_env()
    client = HttpApiClient(env=testnet_env)

    # Alternatively pass no env to get production
    prod_client = HttpApiClient()

    # connect client to different URL
    client = HttpApiClient(api_url='https://yournet.com')

    # get node time
    time = client.get_time()

    # get node info
    node_info = client.get_node_info()

    # get validators
    validators = client.get_validators()

    # get peers
    peers = client.get_peers()

    # get account
    account = client.get_account('tbnb185tqzq3j6y7yep85lncaz9qeectjxqe5054cgn')

    # get account sequence
    account_seq = client.get_account_sequence('tbnb185tqzq3j6y7yep85lncaz9qeectjxqe5054cgn')

    # get markets
    markets = client.get_markets()

    # get fees
    fees = client.get_fees()

    # get order book
    order_book = client.get_order_book('NNB-0AD_BNB')

    # get klines
    klines = client.get_klines('NNB-338_BNB', KlineInterval.ONE_DAY)

    # get closed orders
    closed_orders = client.get_closed_orders('tbnb185tqzq3j6y7yep85lncaz9qeectjxqe5054cgn')

    # get open orders
    open_orders = client.get_open_orders('tbnb185tqzq3j6y7yep85lncaz9qeectjxqe5054cgn')

    # get open orders
    ticker = client.get_ticker('NNB-0AD_BNB')

    # get open orders
    trades = client.get_trades(limit=2)

    # get open orders
    order = client.get_order('9D0537108883C68B8F43811B780327CE97D8E01D-2')

    # get open orders
    trades = client.get_trades()

    # get transactions
    transactions = client.get_transactions(address='tbnb1n5znwyygs0rghr6rsydhsqe8e6ta3cqatucsqp')

    # get transaction
    transaction = client.get_transaction('95DD6921370D74D0459590268B439F3DD49F6B1D090121AFE4B2183C040236F3')

See `API <https://python-binance-chain.readthedocs.io/en/latest/binance-chain.html#module-binance_chain>`_ docs for more information.

Async HTTP Client
-----------------

An implementation of the HTTP Client above using aiohttp instead of requests

Use the async `create` classmethod to initialise an instance of the class.

All methods are otherwise the same as the HttpApiClient


.. code:: python

    from binance_chain.http import AsyncHttpApiClient
    from binance_chain.environment import BinanceEnvironment

    loop = None

    async def main():
        global loop

        env = BinanceEnvironment.get_testnet_env()

        # initialise the class using the classmethod
        client = await AsyncHttpApiClient.create(env)
        wallet = Wallet(private_key=priv_key, env=env)

        print(json.dumps(await client.get_time(), indent=2))

        while True:
            print("doing a sleep")
            await asyncio.sleep(20, loop=loop)


    if __name__ == "__main__":

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())


Environments
------------

Binance Chain offers a Production system and Testnet.

If using the Production system there is no need to pass an environment as this is the default.

To create and use the Testnet environment is as easy as

.. code:: python

    from binance_chain.environment import BinanceEnvironment

    # initialise with Testnet environment
    testnet_env = BinanceEnvironment.get_testnet_env()

You may also create your own custom environments, this may be useful such as connecting to a Node RPC client

.. code:: python

    from binance_chain.environment import BinanceEnvironment

    # create custom environment
    my_env = BinanceEnvironment(api_url="<api_url>", wss_url="<wss_url>", hrp="<hrp>")


See `API <https://python-binance-chain.readthedocs.io/en/latest/binance-chain.html#module-binance_chain.environment>`_ docs for more information.

Wallet
------

See `API <https://python-binance-chain.readthedocs.io/en/latest/binance-chain.html#module-binance_chain.wallet>`_ docs for more information.

The wallet is required if you want to place orders, transfer funds or freeze and unfreeze tokens.

You may also use the `Ledger Wallet class <#ledger>`_ to utilise your Ledger Hardware Wallet for signing.

It can be initialised with your private key or your mnemonic phrase.

Note that the BinanceEnvironment used for the wallet must match that of the HttpApiClient, testnet addresses will not
work on the production system.

The Wallet class can also create a new account for you by calling the `Wallet.create_random_wallet()` function,
see examples below


**Initialise from Private Key**

.. code:: python

    from binance_chain.wallet import Wallet
    from binance_chain.environment import BinanceEnvironment

    testnet_env = BinanceEnvironment.get_testnet_env()
    wallet = Wallet('private_key_string', env=testnet_env)
    print(wallet.address)
    print(wallet.private_key)
    print(wallet.public_key_hex)

**Initialise from Mnemonic**

.. code:: python

    from binance_chain.wallet import Wallet
    from binance_chain.environment import BinanceEnvironment

    testnet_env = BinanceEnvironment.get_testnet_env()
    wallet = Wallet.create_wallet_from_mnemonic('mnemonic word string', env=testnet_env)
    print(wallet.address)
    print(wallet.private_key)
    print(wallet.public_key_hex)

**Initialise by generating a random Mneomonic**

.. code:: python

    from binance_chain.wallet import Wallet
    from binance_chain.environment import BinanceEnvironment

    testnet_env = BinanceEnvironment.get_testnet_env(, env=testnet_env)
    wallet = Wallet.create_random_wallet(env=env)
    print(wallet.address)
    print(wallet.private_key)
    print(wallet.public_key_hex)

Broadcast Messages on HttpApiClient
-----------------------------------

See `API <https://python-binance-chain.readthedocs.io/en/latest/binance-chain.html#module-binance_chain.messages>`_ docs for more information.

Requires a Wallet to have been created.

The Wallet will increment the request sequence when broadcasting messages through the HttpApiClient.

If the sequence gets out of sync call `wallet.reload_account_sequence(client)`, where client is an instance of HttpApiClient.

**Place Order**

General case

.. code:: python

    from binance_chain.http import HttpApiClient
    from binance_chain.messages import NewOrderMsg
    from binance_chain.wallet import Wallet

    wallet = Wallet('private_key_string')
    client = HttpApiClient()

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

**Limit Order Buy**

.. code:: python

    from binance_chain.messages import LimitOrderBuyMsg

    limit_order_msg = LimitOrderBuyMsg(
        wallet=wallet,
        symbol='ANN-457_BNB',
        price=0.000396000,
        quantity=12
    )

**Limit Order Sell**

.. code:: python

    from binance_chain.messages import LimitOrderSellMsg

    limit_order_msg = LimitOrderSellMsg(
        wallet=wallet,
        symbol='ANN-457_BNB',
        price=0.000396000,
        quantity=12
    )

**Cancel Order**

.. code:: python

    from binance_chain.http import HttpApiClient
    from binance_chain.messages import CancelOrderMsg
    from binance_chain.wallet import Wallet

    wallet = Wallet('private_key_string')
    client = HttpApiClient()

    # construct the message
    cancel_order_msg = CancelOrderMsg(
        wallet=wallet,
        order_id="order_id_string",
        symbol='ANN-457_BNB',
    )
    # then broadcast it
    res = client.broadcast_msg(cancel_order_msg, sync=True)


**Freeze Tokens**

.. code:: python

    from binance_chain.http import HttpApiClient
    from binance_chain.messages import FreezeMsg
    from binance_chain.wallet import Wallet

    wallet = Wallet('private_key_string')
    client = HttpApiClient()

    # construct the message
    freeze_msg = FreezeMsg(
        wallet=wallet,
        symbol='BNB',
        amount=Decimal(10)
    )
    # then broadcast it
    res = client.broadcast_msg(freeze_msg, sync=True)


**Unfreeze Tokens**

.. code:: python

    from binance_chain.http import HttpApiClient
    from binance_chain.messages import UnFreezeMsg
    from binance_chain.wallet import Wallet

    wallet = Wallet('private_key_string')
    client = HttpApiClient()

    # construct the message
    unfreeze_msg = UnFreezeMsg(
        wallet=wallet,
        symbol='BNB',
        amount=Decimal(10)
    )
    # then broadcast it
    res = client.broadcast_msg(unfreeze_msg, sync=True)


**Transfer Tokens**

.. code:: python

    from binance_chain.http import HttpApiClient
    from binance_chain.messages import TransferMsg
    from binance_chain.wallet import Wallet

    wallet = Wallet('private_key_string')
    client = HttpApiClient()

    transfer_msg = TransferMsg(
        wallet=wallet,
        symbol='BNB',
        amount=1,
        to_address='<to address>',
        memo='Thanks for the beer'
    )
    res = client.broadcast_msg(transfer_msg, sync=True)

**Vote for proposal**

.. code:: python

    from binance_chain.http import HttpApiClient
    from binance_chain.messages import VoteMsg
    from binance_chain.wallet import Wallet
    from binance_chain.constants import VoteOption

    wallet = Wallet('private_key_string')
    client = HttpApiClient()

    vote_msg = VoteMsg(
        wallet=wallet,
        proposal_id=1,
        vote_option=VoteOption.YES
    )
    res = client.broadcast_msg(vote_msg, sync=True)


Sign Transaction
----------------

If you want to simply sign a transaction you can do that as well.

This is a transfer example

.. code:: python

    from binance_chain.messages import TransferMsg, Signature
    from binance_chain.wallet import Wallet

    wallet = Wallet('private_key_string')

    transfer_msg = TransferMsg(
        wallet=wallet,
        symbol='BNB',
        amount=1,
        to_address='<to address>'
    )
    signed_msg = Signature(transfer_msg).sign()



Websockets
----------

See `API <https://python-binance-chain.readthedocs.io/en/latest/binance-chain.html#module-binance_chain.websockets>`_ docs for more information.

.. code:: python

    import asyncio

    from binance_chain.websockets import BinanceChainSocketManager
    from binance_chain.environment import BinanceEnvironment

    testnet_env = BinanceEnvironment.get_testnet_env()

    address = 'tbnb...'
    loop = None

    async def main():
        global loop

        async def handle_evt(msg):
            """Function to handle websocket messages
            """
            print(msg)

        # connect to testnet env
        bcsm = await BinanceChainSocketManager.create(loop, handle_evt, address2, env=testnet_env)

        # subscribe to relevant endpoints
        await bcsm.subscribe_orders(address)
        await bcsm.subscribe_market_depth(["FCT-B60_BNB", "0KI-0AF_BNB"])
        await bcsm.subscribe_market_delta(["FCT-B60_BNB", "0KI-0AF_BNB"])
        await bcsm.subscribe_trades(["FCT-B60_BNB", "0KI-0AF_BNB"])
        await bcsm.subscribe_ticker(["FCT-B60_BNB", "0KI-0AF_BNB"])

        while True:
            print("sleeping to keep loop open")
            await asyncio.sleep(20, loop=loop)


    if __name__ == "__main__":

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

**Unsubscribe**

.. code:: python

    # with an existing BinanceChainSocketManager instance

    await bcsm.unsubscribe_orders()

    # can unsubscribe from a particular symbol, after subscribing to multiple
    await bcsm.subscribe_market_depth(["0KI-0AF_BNB"])


**Close Connection**

.. code:: python

    # with an existing BinanceChainSocketManager instance

    await bcsm.close_connection()


Node RPC HTTP
-------------

See `API <https://python-binance-chain.readthedocs.io/en/latest/binance-chain.html#module-binance_chain.node_rpc>`_ docs for more information.

The binance_chain.http.HttpApiClient has a helper function `get_node_peers()` which returns a list of peers with Node RPC functionality

.. code:: python

    from binance_chain.http import HttpApiClient, PeerType
    from binance_chain.node_rpc import HttpRpcClient

    httpapiclient = HttpApiClient()

    # get a peer that support node requests
    peers = httpapiclient.get_node_peers()
    listen_addr = peers[0]['listen_addr']

    # connect to this peer
    rpc_client = HttpRpcClient(listen_addr)

    # test some endpoints
    abci_info = rpc_client.get_abci_info()
    consensus_state = rpc_client.dump_consensus_state()
    genesis = rpc_client.get_genesis()
    net_info = rpc_client.get_net_info()
    num_unconfirmed_txs = rpc_client.get_num_unconfirmed_txs()
    status = rpc_client.get_status()
    health = rpc_client.get_health()
    unconfirmed_txs = rpc_client.get_unconfirmed_txs()
    validators = rpc_client.get_validators()

    block_height = rpc_client.get_block_height(10)


Node RPC HTTP Async
-------------------

An aiohttp implementation of the Node RPC HTTP API.

Use the async `create` classmethod to initialise an instance of the class.

All methods are the same as the binance_chain.node_rpc.http.HttpRpcClient.

.. code:: python

    from binance_chain.node_rpc.http import AsyncHttpRpcClient
    from binance_chain.http import AsyncHttpApiClient, PeerType
    from binance_chain.environment import BinanceEnvironment

    loop = None

    async def main():
        global loop

        testnet_env = BinanceEnvironment.get_testnet_env()

        # create the client using the classmethod
        http_client = await AsyncHttpApiClient.create(env=testnet_env)

        peers = await http_client.get_node_peers()
        listen_addr = peers[0]['listen_addr']

        rcp_client = await AsyncHttpRpcClient.create(listen_addr)

        print(json.dumps(await rcp_client.get_abci_info(), indent=2))

        while True:
            print("doing a sleep")
            await asyncio.sleep(20, loop=loop)


    if __name__ == "__main__":

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())


Broadcast Messages on Node RPC HTTP Client
------------------------------------------

Requires a Wallet to have been created

The Wallet will increment the request sequence when broadcasting messages through the HttpApiClient.

If the sequence gets out of sync call `wallet.reload_account_sequence(client)`, where client is an instance of HttpApiClient.

**Place Order**

.. code:: python

    from binance_chain.node_rpc import HttpRpcClient
    from binance_chain.messages import LimitOrderBuyMsg
    from binance_chain.wallet import Wallet
    from binance_chain.constants import RpcBroadcastRequestType

    wallet = Wallet('private_key_string')
    rpc_client = HttpRpcClient(listen_addr)

    limit_order_msg = LimitOrderBuyMsg(
        wallet=wallet,
        symbol='ANN-457_BNB',
        price=0.000396000,
        quantity=12
    )

    # then broadcast it, by default in synchronous mode
    res = rpc_client.broadcast_msg(limit_order_msg)

    # alternative async request
    res = rpc_client.broadcast_msg(new_order_msg, request_type=RpcBroadcastRequestType.ASYNC)

    # or commit request
    res = rpc_client.broadcast_msg(new_order_msg, request_type=RpcBroadcastRequestType.COMMIT)

Other messages can be constructed similar to examples above

Node RPC Websockets
-------------------

See `API <https://python-binance-chain.readthedocs.io/en/latest/binance-chain.html#module-binance_chain.node_rpc.websockets>`_ docs for more information.

For subscribe query examples see the `documentation here <https://docs.binance.org/api-reference/node-rpc.html#631-subscribe>`_

.. code:: python

    import asyncio

    from binance_chain.http import HttpApiClient
    from binance_chain.environment import BinanceEnvironment
    from binance_chain.node_rpc.websockets import WebsocketRpcClient

    loop = None

    async def main():
        global loop

        async def handle_evt(msg):
            print(msg)

        # find node peers on testnet
        testnet_env = BinanceEnvironment.get_testnet_env()
        client = HttpApiClient(testnet_env)

        peers = client.get_node_peers()

        # construct websocket listen address - may not be correct
        listen_addr = re.sub(r"^https?:\/\/", "tcp://", peers[0]['listen_addr'])

        # create custom environment for RPC Websocket
        node_env = BinanceEnvironment(
            api_url=testnet_env.api_url,
            wss_url=listen_addr,
            hrp=testnet_env.hrp
        )

        wrc = await WebsocketRpcClient.create(loop, handle_evt, env=node_env)

        await wrc.subscribe("tm.event = 'NewBlock'")
        await wrc.abci_info()

        while True:
            print("sleeping to keep loop open")
            await asyncio.sleep(20, loop=loop)


    if __name__ == "__main__":

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

**Unsubscribe**

.. code:: python

    # with an existing WebsocketRpcClient instance

    await wrc.unsubscribe("tm.event = 'NewBlock'")

**Unsubscribe All**

.. code:: python

    # with an existing WebsocketRpcClient instance

    await wrc.unsubscribe_all()


Depth Cache
-----------

Follow the order book for a specified trading pair.

Note: This may not be 100% reliable as the response info available from Binance Chain may not always match up

.. code:: python


    from binance_chain.depthcache import DepthCacheManager
    from binance_chain.environment import BinanceEnvironment
    from binance_chain.http import HttpApiClient

    dcm = None
    loop = None


    async def main():
        global dcm1, loop

        async def process_depth(depth_cache):
            print("symbol {}".format(depth_cache.symbol))
            print("1: top 5 asks")
            print(depth_cache.get_asks()[:5])
            print("1: top 5 bids")
            print(depth_cache.get_bids()[:5])

        env = BinanceEnvironment.get_testnet_env()
        client = HttpApiClient(env=env)

        dcm = await DepthCacheManager.create(client, loop, "100K-9BC_BNB", process_depth, env=env)

        while True:
            print("doing a sleep")
            await asyncio.sleep(20, loop=loop)


    if __name__ == "__main__":

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())


Signing Service
---------------

A Service to sign and optionally also broadcast messages for you.

The service holds the private keys of the accounts and supplies a username and password to interact with these accounts.

This client re-uses the binance_chain.messages types. In this case no wallet parameter is required.

This client interacts with the `binance-chain-signing-service <https://github.com/sammchardy/binance-chain-signing-service>`_ read the docs there
to create our own signing service.

**Signing and then broadcasting**

.. code:: python

    from binance_chain.messages import NewOrderMsg
    from binance_chain.signing.http import HttpApiSigningClient

    signing_client = HttpApiSigningClient('http://localhost:8000', username='sam', password='mypass')

    # print(client.signing_service_auth())

    new_order_msg = NewOrderMsg(
        symbol='ANN-457_BNB',
        order_type=OrderType.LIMIT,
        side=OrderSide.BUY,
        price=0.000396000,
        quantity=10,
        time_in_force=TimeInForce.GOOD_TILL_EXPIRE
    )
    new_order_hex = signing_client.sign_order(new_order_msg, wallet_name='wallet_1')

the `sign_order` method can also take a binance_chain.messages.LimitOrderBuyMsg or binance_chain.messages.LimitOrderSellMsg instance.


This hex can then be broadcast using the normal HTTP Client like so


.. code:: python

    from binance_chain.http import HttpApiClient
    from binance_chain.environment import BinanceEnvironment

    # initialise with environment that is supported by the signing service wallet
    testnet_env = BinanceEnvironment.get_testnet_env()
    client = HttpApiClient(env=testnet_env)

    res = client.broadcast_hex_msg(new_order_hex['signed_msg'], sync=True)

The signing service supports binance_chain.messages types
NewOrderMsg, CancelOrderMsg, FreezeMsg, UnFreezeMsg and TransferMsg


**Signing and broadcasting in one**

To sign and broadcast an order use the `broadcast_order` method. This returns the response from the Binance Chain exchange.

.. code:: python

    from binance_chain.messages import NewOrderMsg
    from binance_chain.signing.http import HttpApiSigningClient

    signing_client = HttpApiSigningClient('http://localhost:8000', username='sam', password='mypass')

    # print(client.signing_service_auth())

    new_order_msg = NewOrderMsg(
        symbol='ANN-457_BNB',
        order_type=OrderType.LIMIT,
        side=OrderSide.BUY,
        price=0.000396000,
        quantity=10,
        time_in_force=TimeInForce.GOOD_TILL_EXPIRE
    )
    res = signing_client.broadcast_order(new_order_msg, wallet_name='wallet_1')


Async Signing Service
---------------------

Like all other libraries there is an async version.

.. code:: python

    from binance_chain.signing.http import AsyncHttpApiSigningClient
    from binance_chain.http import AsyncHttpApiClient, PeerType
    from binance_chain.environment import BinanceEnvironment

    loop = None

    async def main():
        global loop

        # create the client using the classmethod
        signing_client = await AsyncHttpApiSigningClient.create('http://localhost:8000', username='sam', password='mypass')

        new_order_msg = NewOrderMsg(
            symbol='ANN-457_BNB',
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            price=0.000396000,
            quantity=10,
            time_in_force=TimeInForce.GOOD_TILL_EXPIRE
        )

        # simply sign the message
        sign_res = await signing_client.sign_order(new_order_msg, wallet_name='wallet_1')

        # or broadcast it as well
        broadcast_res = await signing_client.broadcast_order(new_order_msg, wallet_name='wallet_1')

        print(json.dumps(await rcp_client.get_abci_info(), indent=2))

        while True:
            print("doing a sleep")
            await asyncio.sleep(20, loop=loop)


    if __name__ == "__main__":

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

Ledger
------

Sign transactions with your Ledger wallet, supports Ledger Blue, Nano S and Nano X.

Make sure you have registered on Binance Chain with your Ledger address.

Make sure that you have connected your Ledger and are in the Binance Chain app.

Install python-binance-chain with this optional library like so `pip install python-binance-chain[ledger]`

Uses the `btchip-python library <https://github.com/LedgerHQ/btchip-python>`_ if having issues installing check their github page

.. code:: python

    from binance_chain.ledger import getDongle, LedgerApp, LedgerWallet
    from binance_chain.environment import BinanceEnvironment

    dongle = getDongle(debug=True)

    testnet_env = BinanceEnvironment.get_testnet_env()
    app = LedgerApp(dongle, env=testnet_env)

    # get the Ledger Binance app version
    print(app.get_version())

    # Show your address on the Ledger
    print(app.show_address())

    # Get your address and public key from the Ledger
    print(app.get_address())

    # Get your public key from the Ledger
    print(app.get_public_key())


Create a Wallet to use with the HTTP and Node RPC clients

.. code:: python

    # this will prompt you on your Ledger to confirm the address you want to use
    wallet = LedgerWallet(app, env=testnet_env)


    # now create messages and sign them with this wallet
    from binance_chain.http import HttpApiClient
    from binance_chain.messages import NewOrderMsg, OrderType, OrderSide, TimeInForce

    client = HttpApiClient(env=testnet_env)
    new_order_msg = NewOrderMsg(
        wallet=wallet,
        symbol='ANN-457_BNB',
        order_type=OrderType.LIMIT,
        side=OrderSide.BUY,
        price=0.000396000,
        quantity=10,
        time_in_force=TimeInForce.GOOD_TILL_EXPIRE
    )
    new_order_res = client.broadcast_msg(new_order_msg, sync=True)

    print(new_order_res)


Requests and AioHTTP Settings
-----------------------------

`python-binance-chain` uses `requests <http://docs.python-requests.org>`_ and `aiohttp <https://github.com/aio-libs/aiohttp>`_ libraries.

You can set custom requests parameters for all API calls when creating any of the http clients.

.. code:: python

    client = HttpApiClient(request_params={"verify": False, "timeout": 20})

Check out either the `requests documentation <http://docs.python-requests.org>`_ or `aiohttp documentation <https://github.com/aio-libs/aiohttp>`_ for all options.

**Proxy Settings**

You can use the settings method above

.. code:: python

    proxies = {
        'http': 'http://10.10.1.10:3128',
        'https': 'http://10.10.1.10:1080'
    }

    # in the Client instantiation
    client = HttpApiClient(request_params={'proxies': proxies})

Or set an environment variable for your proxy if required to work across all requests.

An example for Linux environments from the `requests Proxies documentation <http://docs.python-requests.org/en/master/user/advanced/#proxies>`_ is as follows.

.. code-block:: bash

    $ export HTTP_PROXY="http://10.10.1.10:3128"
    $ export HTTPS_PROXY="http://10.10.1.10:1080"

For Windows environments

.. code-block:: bash

    C:\>set HTTP_PROXY=http://10.10.1.10:3128
    C:\>set HTTPS_PROXY=http://10.10.1.10:1080


Running Tests
-------------

.. code-block:: bash

    git clone https://github.com/sammchardy/python-binance-chain.git
    cd python-binance-chain
    pip install -r test-requirements.txt

    python -m pytest tests/


Donate
------

If this library helped you out feel free to donate.

- ETH: 0xD7a7fDdCfA687073d7cC93E9E51829a727f9fE70
- NEO: AVJB4ZgN7VgSUtArCt94y7ZYT6d5NDfpBo
- LTC: LPC5vw9ajR1YndE1hYVeo3kJ9LdHjcRCUZ
- BTC: 1Dknp6L6oRZrHDECRedihPzx2sSfmvEBys

Thanks
------

`Sipa <https://github.com/sipa/bech32>` for python reference implementation for Bech32 and segwit addresses


Other Exchanges
---------------

If you use `Binance <https://www.binance.com/?ref=10099792>`_ check out my `python-binance <https://github.com/sammchardy/python-binance>`_ library.

If you use `Kucoin <https://www.kucoin.com/ucenter/signup?rcode=E42cWB>`_ check out my `python-kucoin <https://github.com/sammchardy/python-kucoin>`_ library.

If you use `Allcoin <https://www.allcoin.com/Account/RegisterByPhoneNumber/?InviteCode=MTQ2OTk4MDgwMDEzNDczMQ==>`_ check out my `python-allucoin <https://github.com/sammchardy/python-allcoin>`_ library.

If you use `IDEX <https://idex.market>`_ check out my `python-idex <https://github.com/sammchardy/python-idex>`_ library.

If you use `BigONE <https://big.one>`_ check out my `python-bigone <https://github.com/sammchardy/python-bigone>`_ library.

.. image:: https://analytics-pixel.appspot.com/UA-111417213-1/github/python-kucoin?pixel
