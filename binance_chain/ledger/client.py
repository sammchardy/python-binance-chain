import re
import binascii
from typing import Optional

from btchip.btchip import writeUint32LE, BTChipException

from binance_chain.environment import BinanceEnvironment
from binance_chain.ledger.exceptions import LedgerRequestException


class LedgerApp:

    BNC_CLA = 0xbc
    BNC_INS_GET_VERSION = 0x00
    BNC_INS_PUBLIC_KEY_SECP256K1 = 0x01
    BNC_INS_SIGN_SECP256K1 = 0x02
    BNC_INS_SHOW_ADDR_SECP256K1 = 0x03
    BNC_INS_GET_ADDR_SECP256K1 = 0x04
    SUCCESS_CODE = 0x9000

    CHUNK_SIZE = 250
    HD_PATH = "44'/714'/0'/0/0"

    def __init__(self, dongle, env: Optional[BinanceEnvironment] = None):
        self._dongle = dongle
        self._path = LedgerApp.HD_PATH
        self._env = env or BinanceEnvironment.get_production_env()
        self._hrp = self._env.hrp

    def _exchange(self, apdu):
        apdu_data = bytearray(apdu)
        try:
            response = self._dongle.exchange(apdu_data)
        except BTChipException as e:
            if e.message.startswith('Invalid status'):
                raise LedgerRequestException(e.sw, binascii.hexlify(apdu_data))
            else:
                raise e

        return response

    def get_version(self) -> dict:
        """Gets the version of the Ledger app that is currently open on the device.

        .. code:: python

            version = client.get_version()

        :return: API Response

        .. code:: python

            {'testMode': False, 'version': '1.1.3', 'locked': False}

        """
        result = {}
        apdu = [self.BNC_CLA, self.BNC_INS_GET_VERSION, 0x00, 0x00, 0x00]
        response = self._exchange(apdu)

        result['testMode'] = (response[0] == 0xFF)
        result['version'] = "%d.%d.%d" % (response[1], response[2], response[3])
        result['locked'] = bool(response[4])
        return result

    def get_public_key(self) -> str:
        """Gets the public key from the Ledger app that is currently open on the device.

        .. code:: python

            public_key = client.get_public_key()

        :return: API Response

        .. code:: python

            '<public_key>'

        """
        dongle_path = self._parse_hd_path(self._path)
        apdu = [self.BNC_CLA, self.BNC_INS_PUBLIC_KEY_SECP256K1, 0x00, 0x00, len(dongle_path)]
        apdu.extend(dongle_path)
        response = self._exchange(apdu)

        return response[0: 1 + 64]

    def show_address(self):
        """Shows the user's address for the given HD path on the device display.

        .. code:: python

            client.show_address()

        :return: None


        """
        dongle_path = self._parse_hrp(self._hrp) + self._parse_hd_path(self._path)
        apdu = [self.BNC_CLA, self.BNC_INS_SHOW_ADDR_SECP256K1, 0x00, 0x00, len(dongle_path)]
        apdu.extend(dongle_path)
        self._exchange(apdu)

    def get_address(self) -> dict:
        """Gets the address and public key from the Ledger app that is currently open on the device.

        .. code:: python

            address = client.get_address()

        :return: API Response

        .. code:: python

            {'pk': '<public_key>', 'address': '<address>'}

        """
        dongle_path = self._parse_hrp(self._hrp) + self._parse_hd_path(self._path)
        apdu = [self.BNC_CLA, self.BNC_INS_GET_ADDR_SECP256K1, 0x00, 0x00, len(dongle_path)]
        apdu.extend(dongle_path)
        response = self._exchange(apdu)
        return {
            'pk': response[0: 1 + 32],
            'address': response[1 + 32:].decode()
        }

    def _get_sign_chunks(self, msg: bytes):
        chunks = [self._parse_hd_path(self._path)]
        chunks += [msg[i:i + self.CHUNK_SIZE] for i in range(0, len(msg), self.CHUNK_SIZE)]
        return chunks

    def sign(self, msg: bytes) -> str:
        """Sends a transaction sign doc to the Ledger app to be signed.

        .. code:: python

            address = client.get_address()

        :return: str

        .. code:: python

            '<signed message hash>'

        """
        chunks = self._get_sign_chunks(msg)
        response = ''
        for idx, chunk in enumerate(chunks):
            apdu = [self.BNC_CLA, self.BNC_INS_SIGN_SECP256K1, idx + 1, len(chunks), len(chunk)]
            apdu.extend(chunk)
            response = self._exchange(apdu)

        if response[0] != 0x30:
            raise Exception("Ledger assertion failed: Expected a signature header of 0x30")

        # decode DER format
        r_offset = 4
        r_len = response[3]
        s_len = response[4 + r_len + 1]
        s_offset = len(response) - s_len

        if r_len == 33:
            r_offset += 1
            r_len -= 1

        if s_len == 3:
            s_offset += 1

        sig_r = response[r_offset: r_offset + r_len]
        sig_s = response[s_offset:]

        return sig_r + sig_s

    def _parse_hd_path(self, path):
        if len(path) == 0:
            return bytearray([0])
        result = []
        elements = path.split('/')
        if len(elements) > 10:
            raise BTChipException("Path too long")
        for pathElement in elements:
            element = re.split('\'|h|H', pathElement)
            if len(element) == 1:
                writeUint32LE(int(element[0]), result)
            else:
                writeUint32LE(0x80000000 | int(element[0]), result)
        return bytearray([len(elements)] + result)

    def _parse_hrp(self, hrp):
        return bytearray([len(hrp)]) + hrp.encode()
