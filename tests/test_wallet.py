import pytest

from binance_chain.wallet import Wallet
from binance_chain.environment import BinanceEnvironment
from binance_chain.client import HttpApiClient


class TestWallet:

    @pytest.fixture()
    def private_key(self):
        return '3dcc267e1f7edca86e03f0963b2d0b7804552d3014caddcfc435a4d7bc240cf5'

    @pytest.fixture()
    def mnemonic(self):
        return ('smart depend recycle toward already roof country frost field dose joke zero start notable vote '
                'eight symptom suffer camp milk dream swear wrap accident')

    @pytest.fixture()
    def env(self):
        return BinanceEnvironment.get_testnet_env()

    @pytest.fixture()
    def httpclient(self, env):
        return HttpApiClient(env=env)

    def test_wallet_create_from_private_key(self, private_key, env):
        wallet = Wallet(private_key=private_key, env=env)

        assert wallet
        assert wallet.public_key_hex == b'02cce2ee4e37dc8c65d6445c966faf31ebfe578a90695138947ee7cab8ae9a2c08'
        assert wallet.address == 'tbnb10a6kkxlf823w9lwr6l9hzw4uyphcw7qzrud5rr'

    def test_wallet_initialise(self, private_key, env, httpclient):

        wallet = Wallet(private_key=private_key, env=env)

        wallet.initialise_wallet(httpclient)

        assert wallet.sequence is not None
        assert wallet.account_number is not None
        assert wallet.chain_id is not None

    def test_initialise_from_mnemonic(self, private_key, mnemonic, env):

        wallet = Wallet.create_wallet_from_mnemonic(mnemonic, env=env)

        assert wallet.private_key == private_key
        assert wallet.public_key_hex == b'02cce2ee4e37dc8c65d6445c966faf31ebfe578a90695138947ee7cab8ae9a2c08'
        assert wallet.address == 'tbnb10a6kkxlf823w9lwr6l9hzw4uyphcw7qzrud5rr'

    def test_initialise_from_random_mnemonic(self, env):
        wallet = Wallet.create_random_wallet(env=env)

        assert wallet
        assert wallet.private_key is not None
        assert wallet.public_key_hex is not None
        assert wallet.address is not None
