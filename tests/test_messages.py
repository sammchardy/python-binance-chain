import pytest
import binascii
from collections import OrderedDict

from binance_chain.messages import PubKeyMsg, NewOrderMsg, CancelOrderMsg, TransferMsg
from binance_chain.environment import BinanceEnvironment
from binance_chain.wallet import Wallet
from binance_chain.utils.encode_utils import varint_encode
from binance_chain.constants import OrderType, OrderSide, TimeInForce


class TestMessages:

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
    def wallet(self, private_key, env):
        wallet = Wallet(private_key=private_key, env=env)
        wallet._address = 'tbnb10a6kkxlf823w9lwr6l9hzw4uyphcw7qzrud5rr'
        return wallet

    def test_public_key_message_protobuf(self, wallet):

        pkm = PubKeyMsg(wallet)

        assert pkm.to_protobuf() == wallet.public_key

    def test_public_key_message_amino(self, wallet):

        pkm = PubKeyMsg(wallet)

        type_bytes = binascii.unhexlify(PubKeyMsg.AMINO_MESSAGE_TYPE)
        len_bytes = varint_encode(len(wallet.public_key))

        assert pkm.to_amino() == type_bytes + len_bytes + wallet.public_key

    def test_new_order_message_dict(self, wallet):

        wallet._account_number = 23452
        wallet._sequence = 2

        symbol = 'ANN-457_BNB'
        order_type = OrderType.LIMIT
        order_type_expected = 2
        order_side = OrderSide.BUY
        order_side_expected = 1
        price = 0.000396000
        expected_price = 39600
        quantity = 10
        expected_quantity = 1000000000
        time_in_force = TimeInForce.GOOD_TILL_EXPIRE
        time_in_force_expected = 1

        msg = NewOrderMsg(
            wallet=wallet,
            symbol=symbol,
            order_type=order_type,
            side=order_side,
            price=price,
            quantity=quantity,
            time_in_force=time_in_force
        )

        expected = OrderedDict([
            ('id', wallet.generate_order_id()),
            ('ordertype', order_type_expected),
            ('price', expected_price),
            ('quantity', expected_quantity),
            ('sender', wallet.address),
            ('side', order_side_expected),
            ('symbol', symbol),
            ('timeinforce', time_in_force_expected),
        ])

        assert msg.to_dict() == expected

    def test_new_order_message_hex(self, wallet):

        wallet._account_number = 23452
        wallet._sequence = 2

        symbol = 'ANN-457_BNB'
        order_type = OrderType.LIMIT
        order_side = OrderSide.BUY
        price = 0.000396000
        quantity = 10
        time_in_force = TimeInForce.GOOD_TILL_EXPIRE

        msg = NewOrderMsg(
            wallet=wallet,
            symbol=symbol,
            order_type=order_type,
            side=order_side,
            price=price,
            quantity=quantity,
            time_in_force=time_in_force
        )

        expected = (b'db01f0625dee0a63ce6dc0430a147f756b1be93aa2e2fdc3d7cb713abc206f877802122a3746373536423142453'
                    b'93341413245324644433344374342373133414243323036463837373830322d331a0b414e4e2d3435375f424e42'
                    b'2002280130b0b502388094ebdc03400112700a26eb5ae9872102cce2ee4e37dc8c65d6445c966faf31ebfe578a9'
                    b'0695138947ee7cab8ae9a2c081240ad219de59c60637d642a684a9d56e4a2d189a2bb2a9028d0f4664206540bee'
                    b'763a62c3ce0ea0069f6e81f0733791c9b2a0e883c66aa6cc732f8ce92829e0b278189cb7012002')

        print(msg.to_hex_data())

        assert msg.to_hex_data() == expected

    def test_cancel_order_message_dict(self, wallet):

        wallet._account_number = 23452
        wallet._sequence = 2

        symbol = 'ANN-457_BNB'
        order_id = '7F756B1BE93AA2E2FDC3D7CB713ABC206F877802-3'

        msg = CancelOrderMsg(
            wallet=wallet,
            symbol=symbol,
            order_id=order_id
        )

        expected = OrderedDict([
            ('refid', order_id),
            ('sender', wallet.address),
            ('symbol', symbol),
        ])

        assert msg.to_dict() == expected

    def test_cancel_order_message_hex(self, wallet):

        wallet._account_number = 23452
        wallet._sequence = 2

        symbol = 'ANN-457_BNB'
        order_id = '7F756B1BE93AA2E2FDC3D7CB713ABC206F877802-3'

        msg = CancelOrderMsg(
            wallet=wallet,
            symbol=symbol,
            order_id=order_id
        )

        print(msg.to_hex_data())
        expected = (b'cb01f0625dee0a53166e681b0a147f756b1be93aa2e2fdc3d7cb713abc206f877802120b414e4e2d3435375f424e'
                    b'421a2a374637353642314245393341413245324644433344374342373133414243323036463837373830322d3312'
                    b'700a26eb5ae9872102cce2ee4e37dc8c65d6445c966faf31ebfe578a90695138947ee7cab8ae9a2c08124031640a'
                    b'1f18daef6a36aeef358ebe559ae34b97c73947915abad91b5c244426ce1130b0425c73d6ebdc7720e2c48613d8e8'
                    b'26a7434e3899e317543f25bf6f63c1189cb7012002')

        assert msg.to_hex_data() == expected

    def test_transfer_message_hex(self, wallet):

        wallet._account_number = 23452
        wallet._sequence = 2

        symbol = 'BNB'
        to_address = 'tbnb10a6kkxlf823w9lwr6l9hzw4uyphcw7qzrud5rr'
        amount = 1

        msg = TransferMsg(
            wallet=wallet,
            symbol=symbol,
            to_address=to_address,
            amount=amount
        )

        expected = (b'c401f0625dee0a4c2a2c87fa0a220a147f756b1be93aa2e2fdc3d7cb713abc206f877802120a0a03424e421080c2d7'
                    b'2f12220a147f756b1be93aa2e2fdc3d7cb713abc206f877802120a0a03424e421080c2d72f12700a26eb5ae9872102'
                    b'cce2ee4e37dc8c65d6445c966faf31ebfe578a90695138947ee7cab8ae9a2c081240d3dab13ba287b21467e735f2db'
                    b'5385479ada835d22cb59721682e53e696d807c6401ae48c51a898582baec46a1906d9448b5150f7c0322181101257d'
                    b'cc917fd2189cb7012002')

        assert msg.to_hex_data() == expected
