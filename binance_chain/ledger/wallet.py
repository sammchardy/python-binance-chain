from typing import Optional

from binance_chain.environment import BinanceEnvironment
from binance_chain.wallet import BaseWallet
from binance_chain.ledger.client import LedgerApp
from binance_chain.utils.segwit_addr import address_from_public_key


class LedgerWallet(BaseWallet):

    def __init__(self, app: LedgerApp, env: Optional[BinanceEnvironment] = None):
        super().__init__(env)
        self._app = app
        self._public_key = self._app.get_public_key()
        print(self._public_key)
        self._address = address_from_public_key(self._public_key, self._env.hrp)
        print(self._address)

    def sign_message(self, msg_bytes):
        return self._app.sign(msg_bytes)
