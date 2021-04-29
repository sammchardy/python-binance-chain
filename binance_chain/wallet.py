import binascii
from enum import Enum
from typing import Optional

from secp256k1 import PrivateKey
from mnemonic import Mnemonic
from pycoin.symbols.btc import network

from binance_chain.utils.segwit_addr import address_from_public_key, decode_address
from binance_chain.environment import BinanceEnvironment


class MnemonicLanguage(str, Enum):
    ENGLISH = 'english'
    FRENCH = 'french'
    ITALIAN = 'italian'
    JAPANESE = 'japanese'
    KOREAN = 'korean'
    SPANISH = 'spanish'
    CHINESE = 'chinese_traditional'
    CHINESE_SIMPLIFIED = 'chinese_simplified'


class BaseWallet:

    HD_PATH = "44'/714'/0'/0/{id}"

    def __init__(self, env: Optional[BinanceEnvironment] = None):
        self._env = env or BinanceEnvironment.get_production_env()
        self._public_key = None
        self._address = None
        self._account_number = None
        self._sequence = None
        self._chain_id = None
        self._http_client = None

    def initialise_wallet(self):
        if self._account_number:
            return
        account = self._get_http_client().get_account(self._address)

        self._account_number = account['account_number']
        self._sequence = account['sequence']

        node_info = self._get_http_client().get_node_info()
        self._chain_id = node_info['node_info']['network']

    def increment_account_sequence(self):
        if self._sequence:
            self._sequence += 1

    def decrement_account_sequence(self):
        if self._sequence:
            self._sequence -= 1

    def reload_account_sequence(self):
        sequence_res = self._get_http_client().get_account_sequence(self._address)
        self._sequence = sequence_res['sequence']

    def generate_order_id(self):
        return f"{binascii.hexlify(self.address_decoded).decode().upper()}-{(self._sequence + 1)}"

    def _get_http_client(self):
        if not self._http_client:
            from binance_chain.http import HttpApiClient
            self._http_client = HttpApiClient(self._env)
        return self._http_client

    @property
    def env(self):
        return self._env

    @property
    def address(self):
        return self._address

    @property
    def address_decoded(self):
        return decode_address(self._address)

    @property
    def public_key(self):
        return self._public_key

    @property
    def public_key_hex(self):
        return binascii.hexlify(self._public_key)

    @property
    def account_number(self):
        return self._account_number

    @property
    def sequence(self):
        return self._sequence

    @property
    def chain_id(self):
        return self._chain_id

    def sign_message(self, msg_bytes):
        raise NotImplementedError


class Wallet(BaseWallet):
    """
    Usage example:

    m = Wallet.create_random_mnemonic() # 12 words
    p = 'my secret passphrase' # bip39 passphrase

    # Store <m> and <p> somewhere safe

    wallet1 = Wallet.create_wallet_from_mnemonic(m, passphrase=p, child=0, env=testnet_env)
    wallet2 = Wallet.create_wallet_from_mnemonic(m, passphrase=p, child=1, env=testnet_env)
    ...

    """

    HD_PATH = "44'/714'/0'/0/{id}"

    def __init__(self, private_key, env: Optional[BinanceEnvironment] = None):
        super().__init__(env)
        self._private_key = private_key
        self._pk = PrivateKey(bytes(bytearray.fromhex(self._private_key)))
        self._public_key = self._pk.pubkey.serialize(compressed=True)
        self._address = address_from_public_key(self._public_key, self._env.hrp)

    @classmethod
    def create_random_wallet(cls, language: MnemonicLanguage = MnemonicLanguage.ENGLISH,
                             env: Optional[BinanceEnvironment] = None):
        """Create wallet with random mnemonic code

        :return: initialised Wallet
        """
        phrase = cls.create_random_mnemonic(language)
        return cls.create_wallet_from_mnemonic(phrase, env=env)

    @classmethod
    def create_wallet_from_mnemonic(cls, mnemonic: str,
                                    passphrase: Optional[str] = '',
                                    child: Optional[int] = 0,
                                    env: Optional[BinanceEnvironment] = None):
        """Create wallet from mnemonic, passphrase and child wallet id

        :return: initialised Wallet
        """
        if type(child) != int:
            raise TypeError("Child wallet id should be of type int")

        seed = Mnemonic.to_seed(mnemonic, passphrase)
        new_wallet = network.keys.bip32_seed(seed)
        child_wallet = new_wallet.subkey_for_path(Wallet.HD_PATH)
        # convert secret exponent (private key) int to hex
        key_hex = format(child_wallet.secret_exponent(), 'x')
        return cls(key_hex, env=env)

    @classmethod
    def create_random_mnemonic(cls, language: MnemonicLanguage = MnemonicLanguage.ENGLISH):
        """Create random mnemonic code

        :return: str, mnemonic phrase
        """
        m = Mnemonic(language.value)
        phrase = m.generate()
        return phrase

    @property
    def private_key(self):
        return self._private_key

    def sign_message(self, msg_bytes):
        # check if ledger wallet
        sig = self._pk.ecdsa_sign(msg_bytes)
        return self._pk.ecdsa_serialize_compact(sig)
