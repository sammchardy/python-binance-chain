import pytest

from binance_chain.wallet import Wallet
from binance_chain.environment import BinanceEnvironment
from binance_chain.http import HttpApiClient


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

    def test_wallet_create_from_private_key(self, private_key, env):
        wallet = Wallet(private_key=private_key, env=env)

        assert wallet
        assert wallet.public_key_hex == b'02cce2ee4e37dc8c65d6445c966faf31ebfe578a90695138947ee7cab8ae9a2c08'
        assert wallet.address == 'tbnb10a6kkxlf823w9lwr6l9hzw4uyphcw7qzrud5rr'

    def test_wallet_initialise(self, private_key, env):

        wallet = Wallet(private_key=private_key, env=env)

        wallet.initialise_wallet()

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
        assert wallet.public_key is not None
        assert wallet.public_key_hex is not None
        assert wallet.address is not None

    def test_wallet_sequence_increment(self, private_key, env):

        wallet = Wallet(private_key=private_key, env=env)

        wallet._sequence = 100

        wallet.increment_account_sequence()

        assert wallet.sequence == 101

    def test_wallet_sequence_decrement(self, private_key, env):
        wallet = Wallet(private_key=private_key, env=env)

        wallet._sequence = 100

        wallet.decrement_account_sequence()

        assert wallet.sequence == 99

    def test_wallet_reload_sequence(self, private_key, env):
        wallet = Wallet(private_key=private_key, env=env)

        wallet.initialise_wallet()
        account_sequence = wallet.sequence

        wallet.increment_account_sequence()

        wallet.reload_account_sequence()

        assert wallet.sequence == account_sequence

    def test_generate_order_id(self, private_key, env):
        wallet = Wallet(private_key=private_key, env=env)

        wallet.initialise_wallet()

        order_id = wallet.generate_order_id()

        assert order_id == f"7F756B1BE93AA2E2FDC3D7CB713ABC206F877802-{wallet.sequence + 1}"

    def test_sign_message(self, private_key, env):
        wallet = Wallet(private_key=private_key, env=env)

        expected = (b'\xd9\x01\x02\xab\x13\xfd^4Ge\x82\xa9\xee\x82\xb5\x8c\xa9\x97}\xf9t\xa9\xc7\nC\xee\xfd\x8bG'
                    b'\x95N\xe84\xfc\x17\xc0JE\x9a.\xe2\xbb\xa3\x14\xde$\x07\t\xbbB\xeb\xe2\xfb\x1e\xa1dc\x9d\xba'
                    b'\xd2\xfa\xe3\xb6\xc1')
        assert wallet.sign_message(b"testmessage") == expected
