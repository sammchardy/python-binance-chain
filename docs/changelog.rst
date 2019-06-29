Changelog
=========

v0.1.20 - 2019-06-29
^^^^^^^^^^^^^^^^^^^^

**Added**

- Multi Transfer Msg option

**Fixed**

- Response code of 0 for http requests

v0.1.19 - 2019-04-30
^^^^^^^^^^^^^^^^^^^^

**Added**

- Shuffling of peer nodes in the Pooled HTTP RPC Node client

v0.1.18 - 2019-04-29
^^^^^^^^^^^^^^^^^^^^

**Added**

- Advanced async Pooled HTTP RPC Node client spreading requests over available peers

**Updated**

- RPC request id behaviour to work across multiple connections

v0.1.17 - 2019-04-29
^^^^^^^^^^^^^^^^^^^^

**Added**

- UltraJson ultra fast JSON parser library
- Docs for requests/aiohttp params and proxy support
- more docs and tests

**Fixed**

- DepthCache close method

v0.1.16 - 2019-04-28
^^^^^^^^^^^^^^^^^^^^

**Added**

- Vote transaction type
- Simple transaction signing example

**Fixed**

- Depth Cache doesn't wait for websocket messages before outputting

v0.1.13 - 2019-04-28
^^^^^^^^^^^^^^^^^^^^

**Added**

- `get_address` function for Ledger hardware wallet
- better error handling and parsing of Ledger hardware wallet responses

v0.1.12 - 2019-04-27
^^^^^^^^^^^^^^^^^^^^

**Added**

- Ledger Hardware wallet support for signing transactions

v0.1.10 - 2019-04-24
^^^^^^^^^^^^^^^^^^^^

**Fixed**

- Connecting to secure and insecure websocket connections

v0.1.9 - 2019-04-23
^^^^^^^^^^^^^^^^^^^

**Added**

- More test coverage including for python 3.7

**Fixed**

- Params in async http client for `get_klines`
- coveralls report
- small fixes

v0.1.8 - 2019-04-21
^^^^^^^^^^^^^^^^^^^

**Added**

- `get_block_exchange_fee` function to Http API Clients
- memo param to Transfer message
- more tests

**Updated**

- Remove jsonrpcclient dependency

**Fixed**

- Use of enums in request params
- Some deprecation warnings

v0.1.7 - 2019-04-18
^^^^^^^^^^^^^^^^^^^

**Updated**

- fix package


v0.1.6 - 2019-04-17
^^^^^^^^^^^^^^^^^^^

**Updated**

- fix package requirement versions

v0.1.5 - 2019-04-17
^^^^^^^^^^^^^^^^^^^

**Fixed**

- signing module imported

v0.1.4 - 2019-04-16
^^^^^^^^^^^^^^^^^^^

**Fixed**

- Issue with protobuf file

v0.1.3 - 2019-04-16
^^^^^^^^^^^^^^^^^^^

**Added**

- Wallet methods for Binance Signing Service v0.0.2

v0.1.2 - 2019-04-14
^^^^^^^^^^^^^^^^^^^

**Added**

- Binance Chain Signing Service Interfaces v0.0.1

**Updated**

- Cleaned up TransferMsg as from_address is found from wallet instance

v0.1.1 - 2019-04-13
^^^^^^^^^^^^^^^^^^^

**Added**

- Broadcast message taking signed hex data

v0.1.0 - 2019-04-11
^^^^^^^^^^^^^^^^^^^

**Added**

- Async versions of HTTP Client
- Async version of Node RPC Client
- Node RPC Websocket client
- Async Depth Cache
- Transfer message implementation
- Message broadcast over Node RPC

v0.0.5 - 2019-04-08
^^^^^^^^^^^^^^^^^^^

**Added**

- All websocket stream endpoints
- Wallet functions to read account and keep track of transaction sequence
- Support for Testnet and Production environments, along with user defined environment
- Helper classes to create limit buy and sell messages

**Updated**

- Refactored modules and tidied up message creation and wallets

v0.0.4 - 2019-04-07
^^^^^^^^^^^^^^^^^^^

**Added**

- Wallet initialise from private key or mnemonic string
- Create wallet by generating a mnemonic

v0.0.3 - 2019-04-06
^^^^^^^^^^^^^^^^^^^

**Added**

- Transaction Broadcasts
- Generated Docs

v0.0.2 - 2019-04-04
^^^^^^^^^^^^^^^^^^^

**Added**

- NodeRPC implementation
- Websockets

v0.0.1 - 2019-02-24
^^^^^^^^^^^^^^^^^^^

- HTTP API Implementation
