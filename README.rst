======================================
Welcome to python-binance-chain v0.0.1
======================================

.. image:: https://img.shields.io/pypi/v/python-binance-chain.svg
    :target: https://pypi.python.org/pypi/python-binance-chain

.. image:: https://img.shields.io/pypi/l/python-binance-chain.svg
    :target: https://pypi.python.org/pypi/python-binance-chain

.. image:: https://img.shields.io/pypi/wheel/python-binance-chain.svg
    :target: https://pypi.python.org/pypi/python-binance-chain

.. image:: https://img.shields.io/pypi/pyversions/python-binance-chain.svg
    :target: https://pypi.python.org/pypi/python-binance-chain

This is an unofficial Python wrapper for the `Binance Chain HTTP API <https://binance-chain.github.io/api-reference/dex-api/paths.html>`_. I am in no way affiliated with Binance, use at your own risk.


PyPi
  https://pypi.python.org/pypi/python-binance-chain

Source code
  https://github.com/sammchardy/python-binance-chain


Features
--------

- Implementation of HTTP endpoints
- Response exception handling

TODO
----

- Implement order broadcast
- Implement websockets etc

Quick Start
-----------

.. code:: bash

    pip install python-binance-chain

.. code:: python

    from binance_chain.client import Client, KlineInterval
    client = Client()

    # connect client to different URL
    client = Client(api_url='https://yournet.com')

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
    print(json.dumps(client.get_ticker('NNB-0AD_BNB'), indent=2))

    # get open orders
    print(json.dumps(client.get_trades(limit=2), indent=2))

    # get open orders
    order = client.get_order('9D0537108883C68B8F43811B780327CE97D8E01D-2')

    # get open orders
    trades = client.get_trades()

    # get transactions
    transactions = client.get_transactions(address='tbnb1n5znwyygs0rghr6rsydhsqe8e6ta3cqatucsqp')

    # get transaction
    transaction = client.get_transaction('95DD6921370D74D0459590268B439F3DD49F6B1D090121AFE4B2183C040236F3')


Donate
------

If this library helped you out feel free to donate.

- ETH: 0xD7a7fDdCfA687073d7cC93E9E51829a727f9fE70
- NEO: AVJB4ZgN7VgSUtArCt94y7ZYT6d5NDfpBo
- LTC: LPC5vw9ajR1YndE1hYVeo3kJ9LdHjcRCUZ
- BTC: 1Dknp6L6oRZrHDECRedihPzx2sSfmvEBys

Other Exchanges
---------------

If you use `Binance <https://www.binance.com/?ref=10099792>`_ check out my `python-binance <https://github.com/sammchardy/python-binance>`_ library.

If you use `Kucoin <https://www.kucoin.com/#/?r=E42cWB>`_ check out my `python-kucoin <https://github.com/sammchardy/python-kucoin>`_ library.

If you use `Allcoin <https://www.allcoin.com/Account/RegisterByPhoneNumber/?InviteCode=MTQ2OTk4MDgwMDEzNDczMQ==>`_ check out my `python-allucoin <https://github.com/sammchardy/python-allcoin>`_ library.

If you use `IDEX <https://idex.market>`_ check out my `python-idex <https://github.com/sammchardy/python-idex>`_ library.

If you use `BigONE <https://big.one>`_ check out my `python-bigone <https://github.com/sammchardy/python-bigone>`_ library.

.. image:: https://analytics-pixel.appspot.com/UA-111417213-1/github/python-kucoin?pixel
