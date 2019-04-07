import binascii
from enum import Enum

from secp256k1 import PrivateKey
from mnemonic import Mnemonic
from pywallet.utils.bip32 import Wallet as Bip32Wallet

from .segwit_addr import address_from_public_key


class MnemonicLanguage(str, Enum):
    ENGLISH = 'english'
    FRENCH = 'french'
    ITALIAN = 'italian'
    JAPANESE = 'japanese'
    KOREAN = 'korean'
    SPANISH = 'spanish'
    CHINESE = 'chinese_traditional'
    CHINESE_SIMPLIFIED = 'chinese_simplified'


class Wallet:

    def __init__(self, private_key):
        self._private_key = private_key
        self._pk = PrivateKey(bytes(bytearray.fromhex(self._private_key)))
        self._public_key = self._pk.pubkey.serialize(compressed=True)
        self._address = address_from_public_key(self._public_key)

    @classmethod
    def create_random_wallet(cls, language: MnemonicLanguage = MnemonicLanguage.ENGLISH):
        """Create wallet with random mnemonic code

        :return:
        """
        m = Mnemonic(language)
        phrase = m.generate()
        return cls.create_wallet_from_mnemonic(phrase)

    @classmethod
    def create_wallet_from_mnemonic(cls, mnemonic: str):
        """Create wallet with random mnemonic code

        :return:
        """
        seed = Mnemonic.to_seed(mnemonic)
        new_wallet = Bip32Wallet.from_master_secret(seed=seed, network='BTC')
        child = new_wallet.get_child_for_path("44'/714'/0'/0/0")
        return cls(child.get_private_key_hex().decode())

    @property
    def address(self):
        return self._address

    @property
    def private_key(self):
        return self._private_key

    @property
    def public_key(self):
        return self._public_key

    @property
    def public_key_hex(self):
        return binascii.hexlify(self._public_key)

    def sign_message(self, msg_bytes):
        sig = self._pk.ecdsa_sign(msg_bytes)
        return self._pk.ecdsa_serialize_compact(sig)
